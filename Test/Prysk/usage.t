-- Setup -----------------------------------------------------------------------

  $ cd "$TESTDIR"

-- Check Incorrect Usage -------------------------------------------------------

Check handling of non-existing option

  $ output="$(icon measure -b '12-12-12-12-12' 2>&1)"
  [2]
  $ printf '%s\n' "$output" | tail -n1
  icon measure: error: one of the arguments -n/--name -m/--mac-address -d/--number is required

Check that incorrect names are handled correctly

  $ output="$(icon measure -n 'TooooLong' 2>&1)"
  [2]
  $ printf '%s\n' "$output" | tail -n1
  icon measure: error: argument -n/--name: “TooooLong” is too long to be a valid name

Check handling of incorrect prescaler value

  $ output="$(icon measure -s 1 2>&1)"
  [2]
  $ printf '%s\n' "$output" | tail -n1
  icon measure: error: argument -s/--prescaler: invalid choice: '?1'? \(choose from '?2.*127'?\) (re)

Check handling of incorrect acquisition time value

  $ output="$(icon measure -a 257 2>&1)"
  [2]
  $ printf '%s\n' "$output" | tail -n1
  icon measure: error: argument -a/--acquisition: invalid choice: '257' \(choose from '?1.*256'?\) (re)

Check handling of incorrect oversampling value

  $ output="$(icon measure -o -1 2>&1)"
  [2]
  $ printf '%s\n' "$output" | tail -n1
  icon measure: error: argument -o/--oversampling: expected one argument

Check handling of incorrect sensor mapping values

  $ output="$(icon measure -1 ' -1' 2>&1)"
  [2]
  $ printf '%s\n' "$output" | tail -n1
  icon measure: error: argument -1/--first-channel: “-1” is not a valid channel number

  $ set -- "-2 256" "-3 nine" "-1 0 -2 0 -3 0 -n Test-STH"
  $ for options in "$@"; do
  >   icon measure $options 2>&1 | tail -n1
  > done
  icon measure: error: argument -2/--second-channel: “256” is not a valid channel number
  icon measure: error: argument -3/--third-channel: “nine” is not a valid channel number
  icon measure: error: At least one measurement channel has to be enabled
