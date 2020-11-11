# Elsa: Checkpoint, Restore, and Migration for JupyterHub

## Abstract

This is a functional prototype of (per-user) checkpoint, restore, and live
migration capabilities for JupyterHub platforms.  Checkpointing -- the
ability to freeze and suspend to disk the running state (contents of memory,
registers, open files, etc.) of a set of processes -- enables the system to
snapshot a user's Jupyter session to permanent storage.  The restore
functionality brings a checkpointed session back to a running state, to
continue where it left off at a later time and potentially on a different
machine.  Finally, live migration enables moving running Jupyter notebook
servers between different machines, transparent to the analysis code and w/o
disconnecting the user.

Our implementation of these capabilities works at the system level, with few
limitations, and typical checkpoint/restore times of O(10s) with a pathway
to O(1s) live migrations.

It opens a myriad of interesting use cases, especially for cloud-based
deployments: from checkpointing idle sessions w/o interruption of the user's
work (achieving cost reductions of 4x or more), execution on spot instances
w.  transparent migration on eviction (with cost reductions up to 3x), to
automated migration of workloads to ideally suited instances (e.g.  moving
an analysis to a machine with more or less RAM or cores based on observed
resource utilization).  The capabilities this project demonstrates can make
science platforms fully elastic and scalable while retaining excellent user
experience.

## Code status

This is beta-level code in terms of features and stability, with pre-alpha
level of code cleanliness, organization, and documentation.  We hope this
will change quickly (in a few weeks time).

If you want to try it out yourself, please contact the authors (e.g., open
an issue) and we'll gelp you get started.

We also have a running instance at:

[https://elsa.dirac.dev](https://elsa.dirac.dev)

If you're interested in trying it out, open an Issue with a subject “Test
Drive: ...short description...”, and describe what you’d be interested in
trying.
