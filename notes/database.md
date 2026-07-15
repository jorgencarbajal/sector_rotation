# SQLite

- Self contained: Has very few dependencies, can run on any operating system.
- Serverless: Instead of communicating with a server via TCP/IP like traditional databases, the process that wants to access the database reads and writes directly from the database files on disk, no intermediary server process. Any program that is able to access the disk is able to use an SQLite database.
- Zero-Configuration: Does not need to be "installed" before it is used. No "setup" procedure.
- Transactional: All changes withing a single transaction in SQLite either occur completely or not at all, even if the act of writing the change out to the disk is interrupted by a program crash, an operating system crash, or a power failure.
