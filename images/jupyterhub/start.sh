#!/bin/bash
#
# (re-)create the users
#
HOMEDIR=/home

echo "================ STARTING JupyterHUB ================"

# Make sure we have jovyan as uid/gid 1000/100
[[ -e "$HOMEDIR/jovyan" ]] || mkdir -p "$HOMEDIR/jovyan"
chown 1000.100 "$HOMEDIR/jovyan"

for USER in $(ls $HOMEDIR); do
	if [[ "$USER" == _* ]]; then
		echo "skipping user $USER (begins with an underscore)"
		continue
	fi

        USERID=$(stat -c '%u' "$HOMEDIR/$USER")
        GROUPID=$(stat -c '%g' "$HOMEDIR/$USER")

        echo "adding user $USER, uid/gid = $USERID/$GROUPID"
        groupadd -g $GROUPID $USER
        useradd -M -s /bin/bash -u $USERID -g $GROUPID $USER
done

#
# run jupyterhub
#
exec jupyterhub
