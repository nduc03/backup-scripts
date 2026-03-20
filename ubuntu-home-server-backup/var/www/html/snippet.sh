adb -d shell pm grant org.kde.kdeconnect_tp android.permission.READ_LOGS;
adb -d shell appops set org.kde.kdeconnect_tp SYSTEM_ALERT_WINDOW allow;
adb -d shell am force-stop org.kde.kdeconnect_tp;