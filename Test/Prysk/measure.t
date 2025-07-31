-- Setup -----------------------------------------------------------------------

  $ cd "$TESTDIR"

-- Check Measure Subcommand ----------------------------------------------------

Reset STU to make sure we do not have higher than usual dataloss

  $ icon stu reset

  $ dataloss=$(icon measure -t 10 -d 0 | grep 'Data Loss' | \
  > sed -E 's/[^0-9]+([0-9]\.[0-9]+)[^0-9]*/\1/')
  $ if [ "$(printf "%s < 10.0\n" "${dataloss}" | bc)" -eq 1 ]; then
  >   printf "Data loss below 10%%\n"
  > else
  >   printf "Data loss equal to or greater than 10%% (%s)\n" "$dataloss"
  > fi
  Data loss below 10%

  $ runtime=$(icoanalyzer Measurement*.hdf5 | 
  >           grep 'Runtime:' | 
  >           sed -E 's/[^0-9]+([0-9]*\.[0-9]+).*/\1/')

Check that runtime is approximately correct

  $ python3 -c "exit(0 if 9.8 < $runtime < 10.1 else 1)"

The file should approximately store 95240 (9524 · 10) values

  $ h5dump -d acceleration -H Measurement*.hdf5 |
  > grep 'DATASPACE  SIMPLE' |
  > sed -E 's/.*DATASPACE  SIMPLE \{ \( ([0-9]+) .*/\1/'
  9[1-6]\d{3} (re)

Check column names

  $ h5dump -d acceleration -H Measurement*.hdf5 | 
  > grep -E '"counter|timestamp|x"' | wc -l | sed 's/\ *//'
  3

Check sample rate attribute

  $ h5dump -a acceleration/Sample_Rate Measurement*.hdf5 |
  > grep '(0)' | sed -E 's/^[^"]*"([^"]+)".*$/\1/'
  9523.81 Hz (Prescaler: 2, Acquisition Time: 8, Oversampling Rate: 64)

Check sensor range attribute

  $ h5dump -a acceleration/Sensor_Range Measurement*.hdf5 |
  > grep '(0)' | sed -E 's/^[^"]*"([^"]+)".*$/\1/'
  .*\d{2,3} g.* (re)

Check start time attribute

  $ timestamp=$(h5dump -a acceleration/Start_Time Measurement*.hdf5 |
  > grep '(0)' | sed -E 's/^[^"]*"([^"]+)".*$/\1/')
  $ python -c "
  > from datetime import datetime
  > delta = datetime.now() - datetime.fromisoformat('$timestamp') 
  > print(delta.seconds < 20)"
  True

-- Cleanup ---------------------------------------------------------------------

  $ rm Measurement*.hdf5
