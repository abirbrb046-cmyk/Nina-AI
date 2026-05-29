[app]
# (str) Title of your application
title = Nina AI
# (str) Package name
package.name = ninaai
# (str) Package domain (needed for android/ios packaging)
package.domain = org.abir
# (str) Source code where the main.py live
source.include_exts = py,png,jpg,kv,atlas,json,ttf
# (list) Application requirements
requirements = python3,kivy,requests,plyer,pyjnius
# (str) Application version
version = 1.0
# (list) Permissions
android.permissions = INTERNET, RECORD_AUDIO
# (int) Target Android API
android.api = 33
# (int) Minimum API required
android.minapi = 21
# (str) Android entry point
android.entrypoint = org.kivy.android.PythonActivity
# (list) Android app theme
android.presplash_color = #FFD1DC