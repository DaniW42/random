## README


## Steps for Autonomous Firmware Conversion (Cisco 2702)

1. **Connect LAN cable** and set your NIC IP (e.g. `10.10.0.70`)
2. **Connect console cable** (baud 9600)
3. **Connect power while holding MODE button**  
   Hold for at least 20 seconds until the LED turns red
4. **Wait until the `ap:` ROMMON prompt appears**

```
set IP_ADDR 10.10.0.20
set NETMASK 255.255.255.0
set TFTP_SERVER 10.10.0.70
set DEFAULT_GATEWAY 10.10.0.1
set DEFAULT_ROUTER 10.10.0.1
set TFTP_FILE ap3g2-k9w7-tar.153-3.JPQ3-2.tar

tftp_init
ether_init
flash_init
```


5. **Check config with:**
```
set
```


6. **NOW run Tftpd64 and set root to directory containing the `.tar` file**

7. **Extract image using:**
```
tar -xtract tftp://10.10.0.70/ap3g2-k9w7-tar.153-3.JPQ3-2.tar flash:
```


8. **Wait until fully extracted**  
*(Monitor progress in Tftpd64 log window)*

9. **Set boot path:**
```
boot
```

10. **Check config with:**
```
set
```

11. **Reboot**
```
boot
```

12. **Don't get confused by 'magic number mismatch: bad mzip file'. Wait.**
```
ap> enable
Password: Cisco
ap#
```

13. **Start configuring.**
