# Connection shim + Action plugin argpsec validation
```
PLAY [mock_host1] ***************************************************************************************************************************************

TASK [cidrblock.conn_test.add] **************************************************************************************************************************
fatal: [mock_host1]: FAILED! => {"changed": false, "connection_details": {"host": "mock_host1", "password": "password", "port": 443, "user": "brad"}, "msg": ["value of second must be one of: 10, 20, got: 2.0"]}
...ignoring

TASK [cidrblock.conn_test.add] **************************************************************************************************************************
fatal: [mock_host1]: FAILED! => {"changed": false, "connection_details": {"host": "mock_host1", "password": "password", "port": 443, "user": "brad"}, "msg": ["parameters are required together: third, fourth"]}
...ignoring

TASK [cidrblock.conn_test.add] **************************************************************************************************************************
ok: [mock_host1]

TASK [assert] *******************************************************************************************************************************************
ok: [mock_host1] => {
    "changed": false,
    "msg": "All assertions passed"
}

TASK [debug] ********************************************************************************************************************************************
ok: [mock_host1] => {
    "result": {
        "changed": false,
        "connection_details": {
            "host": "mock_host1",
            "password": "password",
            "port": 443,
            "user": "brad"
        },
        "failed": false,
        "msg": [],
        "sum": 11.0
    }
}

TASK [cidrblock.conn_test.add] **************************************************************************************************************************
ok: [mock_host1]

TASK [assert] *******************************************************************************************************************************************
ok: [mock_host1] => {
    "changed": false,
    "msg": "All assertions passed"
}

TASK [debug] ********************************************************************************************************************************************
ok: [mock_host1] => {
    "result": {
        "changed": false,
        "connection_details": {
            "host": "mock_host1",
            "password": "password",
            "port": 443,
            "user": "brad"
        },
        "failed": false,
        "msg": [],
        "sum": 42.0
    }
}

PLAY RECAP **********************************************************************************************************************************************
mock_host1                 : ok=8    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=2   

```