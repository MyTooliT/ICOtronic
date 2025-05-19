-- Setup -----------------------------------------------------------------------

  $ cd "$TESTDIR"

-- Check Incorrect Usage -------------------------------------------------------

Check handling of broken sensor mapping

  $ icon measure -1 0 -2 0 -3 0 -d 0
  usage: icon measure [-h] [--log {debug,info,warning,error,critical}]
                      {config,dataloss,list,measure,rename,stu} ...
  icon measure: error: At least one measurement channel has to be enabled
  [2]

Check handling of non-existing option

  $ output="$(icon measure -b '12-12-12-12-12' 2>&1)"
  [2]
  $ printf '%s\n' "$output" | tail -n1
  icon measure: error: one of the arguments -n/--name -m/--mac-address -d/--device-number is required

Check that incorrect names are handled correctly

  $ output="$(icon measure -n 'TooooLong' 2>&1)"
  [2]
  $ printf '%s\n' "$output" | tail -n1
  icon measure: error: argument -n/--name: “TooooLong” is too long to be a valid STH name

Check handling of incorrect prescaler value

  $ output="$(icon measure -s 1 2>&1)"
  [2]
  $ printf '%s\n' "$output" | tail -n1
  icon measure: error: argument -s/--prescaler: invalid choice: '1' (choose from 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127)

Check handling of incorrect acquisition time value

  $ output="$(icon measure -a 257 2>&1)"
  [2]
  $ printf '%s\n' "$output" | tail -n1
  icon measure: error: argument -a/--acquisition: invalid choice: '257' (choose from 1, 2, 3, 4, 8, 16, 32, 64, 128, 256)

Check handling of incorrect oversampling value

  $ output="$(icon measure -o -1 2>&1)"
  [2]
  $ printf '%s\n' "$output" | tail -n1
  icon measure: error: argument -o/--oversampling: expected one argument
