-- Setup -----------------------------------------------------------------------

  $ cd "$TESTDIR"
  $ EXAMPLEDIR=../../icotronic/examples

-- Check Read Data Example -----------------------------------------------------

Read five data values

  $ python $EXAMPLEDIR/read_data.py
  Read data values: \[32\d{3}\.0, 32\d{3}\.0, 32\d{3}\.0]@\d+\.\d+ #\d{1,3} (re)
  Read data values: \[32\d{3}\.0, 32\d{3}\.0, 32\d{3}\.0]@\d+\.\d+ #\d{1,3} (re)
  Read data values: \[32\d{3}\.0, 32\d{3}\.0, 32\d{3}\.0]@\d+\.\d+ #\d{1,3} (re)
  Read data values: \[32\d{3}\.0, 32\d{3}\.0, 32\d{3}\.0]@\d+\.\d+ #\d{1,3} (re)
  Read data values: \[32\d{3}\.0, 32\d{3}\.0, 32\d{3}\.0]@\d+\.\d+ #\d{1,3} (re)