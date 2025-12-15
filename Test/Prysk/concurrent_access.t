-- Setup -----------------------------------------------------------------------

  $ cd "$TESTDIR"
  $ EXAMPLEDIR=../../icotronic/examples

-- Check Concurrent Access Example ---------------------------------------------

Read ADC configuration, while streaming is enabled

  $ python $EXAMPLEDIR/concurrent_access.py
  Prescaler: \d+, Acquisition Time: \d+, Oversampling Rate: \d+, Reference Voltage: \d+(.\d*)? V (re)