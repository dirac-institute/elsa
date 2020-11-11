#!/bin/bash
# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

set -e

#
# (re-)create the users
#
HOMEDIR=/home

# Make sure we have jovyan as uid/gid 1000/100
[[ -e "$HOMEDIR/jovyan" ]] || mkdir -p "$HOMEDIR/jovyan"
chown 1000:100 "$HOMEDIR/jovyan"

# More general based on environment variables? NB_USER=jovyan, 
# NB_UID=100, NB_GID=100 by default
# [[ -e "$HOMEDIR/$NB_USER" ]] || mkdir -p "$HOMEDIR/$NB_USER"
# chown $NB_UID:$NB_GID "$HOMEDIR/$NB_USER"

for USER in $(ls $HOMEDIR); do
	if [[ "$USER" == _* ]]; then
		echo "skipping user $USER (begins with an underscore)"
		continue
	fi
	if [[ "$USER" == jovyan ]]; then
		echo "skipping built-in user jovyan"
		continue
	fi

        USERID=$(stat -c '%u' "$HOMEDIR/$USER")
        GROUPID=$(stat -c '%g' "$HOMEDIR/$USER")

        echo "adding user $USER, uid/gid = $USERID/$GROUPID"
        groupadd -g $GROUPID $USER || true
        useradd -m -s /bin/bash -u $USERID -g $GROUPID -k /etc/skel $USER || true
done

# Exec the specified command or fall back on bash
if [ $# -eq 0 ]; then
    cmd=( "bash" )
else
    cmd=( "$@" )
fi

# Enable sudo if requested
if [[ "$GRANT_SUDO" == "1" || "$GRANT_SUDO" == 'yes' ]]; then
    echo "Granting $NB_USER sudo access and appending $CONDA_DIR/bin to sudo PATH"
    echo "$NB_USER ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/notebook
fi

# Add $CONDA_DIR/bin to sudo secure_path
sed -r "s#Defaults\s+secure_path\s*=\s*\"?([^\"]+)\"?#Defaults secure_path=\"\1:$CONDA_DIR/bin\"#" /etc/sudoers | grep secure_path > /etc/sudoers.d/path

# change directory
cd "/home/$NB_USER"
# show environment (for debugging info)
export

# Exec the command as NB_USER with the PATH and the rest of
# the environment preserved
echo "Executing the command: ${cmd[@]}"
exec sudo -E -H -u $NB_USER PATH=$PATH XDG_CACHE_HOME=/home/$NB_USER/.cache PYTHONPATH=${PYTHONPATH:-} "${cmd[@]}"
