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
