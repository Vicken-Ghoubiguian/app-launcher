# -*- coding: utf-8 -*-
##########################################################
# Cause we need some more services !
# SoftBank Robotics Europe (c) 2016 All Rights Reserved -
##########################################################

# Standard Python lib
import qi
import time
import sys
import os
import base64
import traceback
import json

############################################################################################################

class AppLauncher():

    @qi.nobind
    def __init__(self, session=None):
        self.session = session
        self.module_name = self.__class__.__name__
        #logger.basicConfig(filename=self.module_name+'.log', level=logger.DEBUG)
        self.logger = qi.Logger(self.module_name)
        self.module_name = self.__class__.__name__
        self.logger.info(".: Starting {} :.".format(self.module_name))

        # Init variables
        self.displayedApplication = self._find_app_name()
        self.current_state = qi.Property()
        self.current_state.setValue("")
        self.ping_required = qi.Signal()
        self.previous_state = ""
        self.watchTabCount = 0
        self.current_app = ""
        self.dialogAlwaysRunning = False
        self.subscriber_list = []
        self.robot_is_booting = True
        self.launch_async = False
        self.qiasyncList = []
        self.pages_prefs = True
        self.current_language=""
        self.listTab = []
        self.listApp = []
        self.qiasync_require_ping=[]

        # Init services
        self._connect_services()

        # Sync Preferences
        self._sync_preferences()

        # Connect signals
        self._subscribe_events()

        # Init States
        self._init_states()

        self.logger.info(":::: Started successfully ::::")

    @qi.nobind
    def _find_app_name(self):
        import re
        path = os.path.dirname(os.path.realpath(__file__))
        match = re.search("(?<=/PackageManager/apps/)(?P<uid>[\w\._-]+)", path)
        if match :
            appname = match.group(0)
            self.logger.info("appname is {} ".format(appname))
            return appname
        else:
            appname = "app-launcher"
            self.logger.error("Unable to find app name in path {}".format(path))
            self.logger.info("Default app name is {} ".format(appname))
            return appname

    @qi.nobind
    def _connect_services(self):
        """Connect to all services required by AppLauncher"""
        self.logger.info('Connecting services...')
        self.services_connected = qi.Promise()
        services_connected_fut = self.services_connected.future()

        def get_services():
            """Attempt to get all services"""
            try:
                self.memory = self.session.service('ALMemory')
                self.prefs  = self.session.service("ALPreferenceManager")
                self.pacman = self.session.service('PackageManager')
                self.alife  = self.session.service("ALAutonomousLife")
                self.tablet = self.session.service('ALTabletService')
                self.behman = self.session.service('ALBehaviorManager')
                self.audio  = self.session.service('ALAudioDevice')
                self.dialog = self.session.service('ALDialog')

                self.logger.info('All services are now connected')
                self.services_connected.setValue(True)
                #Init variable state

            except RuntimeError as e:
                self.logger.warning('Missing service:\n {}'.format(e))

        get_services_task = qi.PeriodicTask()
        get_services_task.setCallback(get_services)
        get_services_task.setUsPeriod(int(2*1000000))  # check every 2s
        get_services_task.start(True)
        try:
            services_connected_fut.value(30*1000)  # timeout = 30s
            get_services_task.stop()
        except RuntimeError:
            get_services_task.stop()
            self.logger.error('Failed to reach all services after 30 seconds')
            raise RuntimeError

    @qi.nobind
    def _sync_preferences(self):
        """Sync with preferences. This includes: Settle Time, Hold Time and Sequence Time"""
        self.logger.info('Syncing preferences...')

        domain = "tool.applauncher"
        # Sync Timing Preferences
        try:
            displayedApplication = self.prefs.getValue(domain, 'displayedApplication')
            if displayedApplication:
                self.displayedApplication = displayedApplication
                self.logger.info('Syncing displayed Application...')
        except:
            pass
        # Sync autorun dialog Preferences
        import ast
        try:
            dialogAlwaysRunning = self.prefs.getValue(domain, 'dialogAlwaysRunning')
            if dialogAlwaysRunning:
                self.dialogAlwaysRunning = ast.literal_eval(dialogAlwaysRunning)
                self.logger.info('Syncing Autorun dialog...')
        except:
            pass

        self.logger.info('Preferences synchronized')

    @qi.nobind
    def _sync_pages_prefs(self):
        """Get the robot pages preferences
            to know how to create AppLauncher pages(which pages? which apps?).
            First case: The user has created his own cloud preferences.
                The interface will be built as required.
            Second case: There is no cloud preferences.
                The interface will be built as described in file "defaultPreferences.json"
        """

        self.listTab = []
        self.listApp = []
        # First page is the home page
        self.listTab.append('Home')
        self.listApp.append('Home')

        try:
            # Get all the preferences with 'salesdemo.demo-launcher.pages' as domain
            pages_prefs = self.prefs.getValueList('tool.applauncher.page')
            # Get current robot language
            self.current_language = self.dialog.getLanguage()
            # If there is cloud preferences
            if pages_prefs:
                # For each page in preferences
                for page in pages_prefs :
                    # Double quote are not allowed in cloud preferences, so we use
                    self.pages_prefs = page[1].replace('\'', '"')
                    # simple quote and they are replaced here to stick to json format
                    self.pages_prefs = json.loads(self.pages_prefs)
                    # Fill listTab and listApp of each page according to cloud preferences
                    self._fill_pages_prefs()

                self.logger.info('Cloud Apps Preferences loaded')

            else:
                # Get the path of the file "defaultPreferences.json"
                url = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'html', 'resources','defaultPreferences.json'))

                with open(url) as openUrl:
                    # Load the json
                    defaultPreferences = json.load(openUrl)
                    # For each page in preferences
                    for page in defaultPreferences:

                        self.pages_prefs = page
                        # Fill listTab and listApp of each page according to default preferences
                        self._fill_pages_prefs()
                    openUrl.closed

                self.logger.info('Local Apps Preferences loaded')
        except Exception as e:
            self.logger.error('Exception : '+ str(e))
            self.logger.error('Failed to reach all Pages Preferences')

    @qi.nobind
    def _fill_pages_prefs(self):
        # If the page's title is available in the current robot language
        if self.current_language in self.pages_prefs['title'].keys():
            # It is set to the page's title
            self.listTab.append(self.pages_prefs['title'][self.current_language])
        # Else if, it is availabe in english
        elif 'English' in self.pages_prefs['title'].keys():
            # It is set to the page's title
            self.listTab.append(self.pages_prefs['title']['English'])
        else:
            # Else "current language of the robot missing" is set to the page's title
            self.listTab.append(self.current_language+" missing")

        # Add listApp from preferences
        self.listApp.append(self.pages_prefs['apps'])

    @qi.nobind
    def _subscribe_events(self):
        self.logger.info('Binding signals and events...')

        try:
            # Each time 'AutonomousLife/State' is modified, the method "_life_state_changed" is called
            sigLifeState = self.memory.subscriber('AutonomousLife/State').signal
            conLifeState = sigLifeState.connect(self._life_state_changed)
            self.subscriber_list.append([sigLifeState, conLifeState])

            # Each time 'current_state' is modified, the method "_state_changed" is called
            conCurrentState = self.current_state.connect(self._state_changed)
            self.subscriber_list.append([self.current_state, conCurrentState])

            ###@TODO LATER : écouter pref synchronized?

            self.logger.info('All signals have been binded')
        except Exception, e:
            self.logger.error("Subscribe events error: " +str(e))

    @qi.nobind
    def _unsubscribe_events(self):
        self.logger.info('Disconnecting signals and events...')
        for sig, i in self.subscriber_list :
            try :
                sig.disconnect(i)
            except :
                self.logger.error("error while disconnect")
        self.logger.info('All signals have been disconnected')

    @qi.nobind
    def _init_states(self):
        """Make the initialisation of states variables
        """
        try:
            self.tablet._enableResetTablet(0)
            self.tablet.setVolume(10)
            self.current_state.setValue(self.memory.getData("AutonomousLife/State"))
            self.robot_is_asleep = self.memory.getData("AutonomousLife/Asleep")
            self._set_AppLauncher_state_from_life_state( self.memory.getData("AutonomousLife/State"))
        except Exception, e:
            self.logger.error("Init States error: " +str(e))


    """
        Attached app functions
    """
    @qi.bind(paramsType=(), returnType = qi.Void)
    def _clean_tablet(self):
        self.tablet.cleanWebview()
        self.logger.info("cleanWebview : done")
        self.tablet._clearWebviewCache(1)
        self.logger.info("clearWebviewCache: done")

    @qi.bind(paramsType=(), returnType = qi.Void)
    def display_tablet(self):
        self.logger.info("Displaying tablet ")
        ###@TODO LATER: virer la sync des prefs ici pour l'avoir sur event chgt de pref à la place

        try:
            self._sync_pages_prefs()
            self._clean_tablet()
            # Disable resetTablet(never display the colored bubble)
            self.tablet._enableResetTablet(0)
            #Display the webpage on the tablet
            self.tablet.loadApplication(self.displayedApplication)
            self.tablet.showWebview()
        except Exception as e:
            self.logger.error("Tablet error: "+str(e))

        # If 10 seconds after the display_tablet,
        # the page doesn't ping this service,
        # the tablet will be automaticaly restarted and the page reloaded
        self.launch_async = qi.async(self._watchTabLevel2, delay=10000000)
        self.qiasyncList.append(self.launch_async)

    @qi.nobind
    def start_dialog(self):
        try:
            if self.dialogAlwaysRunning:
                self.logger.info("dialogAlwaysRunning: True")
                self.memory.insertData("Dialog/DoNotStop", 1)
                self.alife.switchFocus("run_dialog_dev/.")
        except Exception as e:
            self.logger.error("Run dialog error: "+str(e))

    @qi.bind(returnType = qi.String, paramsType = [qi.String])
    def package_icon(self, uuid):
        """Get the icon of a package.
        :param uuid: (str) uuid of the package
        :return: (str) a base64-encoded package icon.
        """
        return base64.encodestring(self.pacman.packageIcon(uuid))

    @qi.bind(paramsType=(), returnType = qi.List(qi.String))
    def get_listTab(self):
        """Return the list of pages"""
        return self.listTab

    @qi.bind(paramsType=())
    def get_listApp(self):
        """Return the list of apps"""
        return self.listApp

    @qi.bind(paramsType = [qi.String], returnType = qi.Void)
    def _cleanAndStopPing(self, behavior):
        """Switch life focus to a specific behavior."""
        try:
            self.logger.info("Clean and run:")
            self._clean_tablet()
            self.logger.info("Behavior's path: {}" .format(behavior))

            # Stop all the scheduled display_tablet
            self._qiasyncStop()
            for asyncOrder in self.qiasync_require_ping:
                asyncOrder.cancel()

            self.qiasync_require_ping =[]

        except Exception as e:
            self.logger.error("Stop the scheduled display_tablet got an error: "+str(e))

    @qi.bind(paramsType = [qi.String], returnType = qi.Void)
    def runBehavior(self, behavior):
        try:
            # If an error occurs during launch, the tablet will be displayed again
            app_launched_check = qi.async(self.display_tablet, delay=15000000)
            # Life switch focus to the choosen app
            self.alife.switchFocus(behavior)
            self.logger.info("Switch focus")
            app_launched_check.cancel()
            self.logger.info("Application launch end")

        except Exception as e:
            self.logger.error("Run behavior error: "+str(e))

    @qi.bind(paramsType=(), returnType = qi.Void)
    def stopBehavior(self):
        # Life stop the running app
        self.behman.stopBehavior(self.current_app)
        self.logger.info("Stop behavior: {}" .format(self.current_app))

    @qi.bind(paramsType = [qi.Int32], returnType = qi.Void)
    def adjustVolume(self, diff):
        """Change the robot volume. """
        currentVolume = self.audio.getOutputVolume()
        newVolume = currentVolume + diff
        if newVolume > 100:
            newVolume = 100
        elif newVolume < 20:
            newVolume = 20;
        self.audio.setOutputVolume(newVolume)
        self.logger.info("New volume: {}" .format(newVolume))

    @qi.bind(paramsType=(), returnType = qi.Void)
    def require_ping(self):
        """ Asks the webpage displayed on the tablet for a ping. This will trigger the signal ping_required."""
        self.logger.info("Require_ping Start")
        self.ping_required(1)
        self.logger.info("Require_ping Stop")

    @qi.bind(paramsType = [qi.Int32], returnType = qi.Void)
    def ping(self, delay):
        """To be used by the webpage displayed on the tablet when a ping has been required through the signal ping_requiered. This method is called by the tablet, each time it is called, it stops all the scheduled display_tablet and plan a display_tablet in delay+10 seconds.
If no other ping come after, it means the javascript is no longer available.
So when the delay has elapsed, it will try to display again the tablet.
        """
        self._watchTabLevel1(delay)

    @qi.nobind
    def _watchTabLevel1(self, ask_delay):
        """ This method checks if the page on the Tablet is loaded and the javascript responding.
This method is called by the tablet, each time it is called, it stops all the scheduled display_tablet and plan a display_tablet in delay+10 seconds.
If no other ping come after, it means the javascript is no longer available.
So when the delay has elapsed, it will try to display again the tablet.
        """
    ###@TODO LATER: voir si vraiment utile ou si level2 uniquement?
        qiasync_require_ping = qi.async(self.require_ping, delay=ask_delay*1000)
        self.qiasync_require_ping.append(qiasync_require_ping)

        try:
            self._qiasyncStop()

            if self.current_state.value() == "ready" or self.current_state.value() == "sleeping":
                new_delay = ((ask_delay*1000) + 10000000)
                self.launch_async = qi.async(self.display_tablet, delay=new_delay)
                self.logger.info("qi.async Start")
                self.qiasyncList.append(self.launch_async)
        except:
            self.logger.warning("Unexpected error:")
            traceback.print_exc( sys.exc_info()[2])

    @qi.nobind
    def _watchTabLevel2(self):
        """ If 10 seconds after the display_tablet,
            the page doesn't ping this service, this method is called
            the tablet will be automaticaly restarted and the page reloaded
        """
        self.logger.info("Begin watchTabLevel2")
        self._qiasyncStop()

        self.tablet = self.session.service('ALTabletService')
        self.tablet._restart()
        self.launch_async = qi.async(self.display_tablet, delay=3000000)
        self.qiasyncList.append(self.launch_async)
        self.logger.info("End watchTabLevel2")

    @qi.nobind
    def _qiasyncStop(self):
        """This method stops all the scheduled display_tablet"""
        for asyncOrder in self.qiasyncList:
            asyncOrder.cancel()

        self.qiasyncList =[]
        self.logger.info("qi.async Stop")

    """
        CALLBACK FUNCTIONS
    """

    @qi.nobind
    def _set_current_state(self, new_state):
        """This method checks whether the state is part of the
            permitted states and is different from the current state
        """
        try:
            if(new_state not in ["sleeping", "ready", "running"]):
                raise RuntimeError("Demo state cannot be {}, it must be sleeping, running or ready.".format(new_state))
            if new_state != self.current_state.value():
                self.current_state.setValue(new_state)
        except Exception, e:
            self.logger.error("Set curent state error: " +str(e))

    @qi.nobind
    def _life_state_changed(self, state):
        """This method is called each time Autonomous Life State
            change to call the AppLauncher state setter
        """
        self.logger.info("Life state changed: {}".format(state))

        # Check that the tablet is cleaned and the scheduled display_tablet() and pings are stopped
        cur_app = self.memory.getData("AutonomousLife/NextActivity")
        if state == "interactive" and cur_app != "run_dialog_dev/.":
            self._cleanAndStopPing(cur_app)

        self._set_AppLauncher_state_from_life_state(state)

    @qi.nobind
    def _set_AppLauncher_state_from_life_state(self, autonomouslife_state):
        """This method set the state which is used in the tablet
            javascript to handle what will be displayed according
            to the robot life state.
            There are 3 different states, "sleeping", "ready", "running"
            in the AppLauncher javascript and 4 in ALAutonomousLife
            "solitary", "interactive", "disabled", "safeguard"
        """
        try:
            if autonomouslife_state == "solitary":
                asleep = False
                try:
                    asleep = self.memory.getData("AutonomousLife/Asleep")
                except:
                    self.logger.info("could not read AutonomousLife/Asleep")
                if asleep:
                    self._set_current_state("sleeping")
                else:
                    self._set_current_state("ready")

            elif autonomouslife_state == "interactive":

                try:
                    self.current_app = self.memory.getData("AutonomousLife/NextActivity")
                    self.logger.info("Running {}".format(self.current_app))
                except:
                    self.logger.info("could not read AutonomousLife/NextActivity")

                if self.current_app != "run_dialog_dev/.":
                    self._set_current_state("running")
                else:
                    self._set_current_state("ready")

            elif autonomouslife_state == "disabled":
                self._set_current_state("sleeping")

            elif autonomouslife_state == "safeguard":
                self._set_current_state("sleeping")

        except Exception, e:
            self.logger.error("Set AppLauncher state error: " +str(e))

    @qi.nobind
    def _state_changed(self, current_state):
        """Each time 'current_state' is modified, this method is called
            If the robot is booting, first time current_state change to ready
            it will launch the first display_tablet and the dialog.
            Each time current_state change from "running" to another state
            display_tablet is called.
        """
        try:
            if self.robot_is_booting and current_state == "ready":
                self.robot_is_booting = False
                self.logger.info("Launch display")
                self.display_tablet()
                self.start_dialog()
            elif current_state == self.previous_state:
                pass
            elif self.previous_state == "running":
                self.display_tablet()
                self.start_dialog()
                self.logger.info("previous state running")

            self.previous_state = current_state

        except Exception, e:
            self.logger.error("States changed error: " +str(e))

# ----------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------
def register_as_service(service_class, session):
    """
    Registers a service in naoqi
    """
    service_name = service_class.__name__
    instance = service_class(session)
    try:
        session.registerService(service_name, instance)
        print 'Successfully registered service: {}'.format(service_name)
        return instance
    except RuntimeError:
        print '{} already registered, attempt re-register'.format(service_name)
        for info in session.services():
            try:
                if info['name'] == service_name:
                    session.unregisterService(info['serviceId'])
                    print "Unregistered {} as {}".format(service_name, info['serviceId'])
                    break
            except (KeyError, IndexError):
                pass
        session.registerService(service_name, instance)
        print 'Successfully registered service: {}'.format(service_name)
        return instance

if __name__ == "__main__":
    """
    Registers AppLauncher as a naoqi service.
    """
    app = qi.Application(sys.argv)
    app.start()
    instance = register_as_service(AppLauncher, app.session)
    app.run()
    instance._unsubscribe_events()
# ----------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------
