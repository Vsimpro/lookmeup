#
#   File
#

create_file_table = """
CREATE TABLE IF NOT EXISTS File (

    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    name   TEXT NOT NULL, --
    chunks INT  NOT NULL,
    sha1   TEXT NOT NULL --

);
"""

insert_into_files = """
INSERT INTO File (
    name,
    chunks,
    sha1
) 
VALUES (?, ?, ?);
"""

get_fileid_with_sha = """
SELECT id FROM File WHERE sha1 = ?;
"""

get_name_with_sha = """
SELECT name FROM File WHERE sha1 = ?;
"""


get_size_with_sha = """
SELECT chunks FROM File where sha1 = ?;
"""


#
#   File chunk
#

create_filechunk_table = """
CREATE TABLE IF NOT EXISTS FileChunk (

    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id      INT  NOT NULL,      --
    chunk_id     INT  NOT NULL, --
    chunk_data   TEXT NOT NULL  --

);
"""

insert_into_filechunk = """
INSERT INTO FileChunk (
    file_id,
    chunk_id,
    chunk_data
) 
VALUES (?, ?, ?);
"""

check_filechunks = """
SELECT count(distinct chunk_id) FROM FileChunk WHERE file_id = ?;
""" # Why is this SHA?

get_filechunks = """
SELECT distinct chunk_id, chunk_data FROM FileChunk WHERE file_id = ? AND chunk_id != 0 ORDER BY chunk_id;
""" 

#
#   Sent
#

create_sentlog_table = """
CREATE TABLE IF NOT EXISTS SentLog (

    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id     INT NOT NULL, --
    sent_status INT NOT NULL  -- 1 for sent

);
"""

insert_into_sentlog = """
INSERT INTO SentLog (
    file_id,
    sent_status
) 
VALUES (?, ?);
"""
 
get_sent_status = """
SELECT sent_status FROM SentLog;
"""