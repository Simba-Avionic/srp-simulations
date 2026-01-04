## srp-simulations

Only supports SOME/IP events

# Providing input
In root folder as input.json. (case sensitive)
Format:
service, event, value, seconds_after_start

e.g.
{
  "EnvApp": [
    {
      "event": "newTempEvent_3",
      "value": 72,
      "seconds_after_start": 2
    },
    {
      "event": "newTempEvent_1",
      "value": 35,
      "seconds_after_start": 5
    }
  ],
  "EngineService": [
    {
      "event": "currentmode",
      "value": 2,
      "seconds_after_start": 6
    }
  ]
}


See sample input in input.json


# Generating services
1. Verify that paths in the scripts are correct
2. Use the Makefile 
