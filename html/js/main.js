multipleClick_clickTime = null; multipleClick_target = null; function preventMultipleClick(id) { sameTarget = false; if(id==multipleClick_target) { sameTarget = true; } multipleClick_target = id; fastClick = false; var currentClickTime = new Date(); if (currentClickTime - multipleClick_clickTime < 500) {fastClick = true;} multipleClick_clickTime = currentClickTime; return (sameTarget && fastClick); }
var listTab=[]; var listTabId=[]; var listApp=[]; var listStates=["main_menu", "loading_menu", "onsleep_menu"]; var xi = 2; var nbBehavior = 0; var audio = new Audio('resources/change_screen.ogg'); var color = ['#ee6675','#00979a','#e64d40','#009667','#85c553','#814a74','#f58239'];
var languages = JSON.parse('{"English":"en_US","French":"fr_FR","Japanese":"ja_JP","Chinese":"zh_CN","Spanish":"es_ES","German":"de_DE","Korean":"ko_KR","Italian":"it_IT","Dutch":"nl_NL","Finnish":"fi_FI","Polish":"pl_PL","Russian":"ru_RU","Turkish":"tr_TR","Arabic":"ar_SA","Czech":"cs_CZ","Portuguese":"pt_PT","Brazilian":"pt_BR","Swedish":"sv_SE","Danish":"da_DK","Norwegian":"nn_NO","Greek":"el_GR"}');

function add_div_tab(listTabId){

    var createDivTab ='';
    for (var name in listTabId){
        createDivTab +='<div id="'+listTabId[name]+'"><div id="'+listTabId[name]+'1" class="hex-row"></div><div id="'+listTabId[name]+'2" class="hex-row even"></div></div>';
    }
}

function add_button_home_page(id_div){
    ///@TODO: passer tout en argument au lieu de variables globales
    for (var i = 1; i < listTabId.length; i++) {
        pageId = listTabId[i];
        idElement = listTabId[i]+ make_id();
        nbBehavior = $("."+id_div).length;
        if(nbBehavior%2 == 1) {xi=2;}  else xi=1;
        $("#"+id_div+xi).append(
            '<div class="hex '+id_div+'">'+
                '<div id="'+idElement+'" class="homePageBtn">'+listTab[i]+'</div>'+
            '</div>');
        $('#'+idElement).css('background-color', make_color());   
        show_tab_on_click.call(this, idElement, pageId);     
    }
}

function show_tab_on_click(idElement, pageId){
	//On touch, App's description is displayed below the icon app
    $('body').on('touchstart touchmove click', "#"+idElement, function(){
        if (preventMultipleClick("Element")) return;
        $("#"+idElement).blur();
        audio.play();
        show_tab(pageId);
    });
}

// Display the tab whose id is received
function show_tab(id) {
    var div = null;
    // Hide all tabs
    for (var name in listTabId){
        div = document.getElementById(listTabId[name]);
        div.style.display = "none";
    }
    // Display the  selected tab
    div = document.getElementById(id);
    if(div.style.display=="none") {
        div.style.display = "block";
    } 

    div = document.getElementById('Home');
    // Display Home and Help buttons if the home tab is hidden
    if(div.style.display=="none"){
        $(".home").css('display', 'block');
        $("#btn_help").css('display', 'inline-block');
    }else{
    // Hide those buttons
        $(".home").css('display', 'none');
        $("#btn_help").css('display', 'none');
    }
}

// This fonction is called in each state changed
function stateChanged(state, behaviorName) {
	// Display the window match to the robot state, 
    console.log("State changed:" + state);
    // Ready("main menu with tabs containing the apps"),
    if (state == "ready") display_window("main_menu");
    else if (state == "running") {}							
    // Sleeping("heartRate and wakeup button"),
    else if (state == "sleeping")   display_window("onsleep_menu");
    // Laoding("spinner")
    else display_window("loading_menu");
}

// Display the window match to received id and hide the others
function display_window(id){
    var div = null;											
    for (var state in listStates){							
        div = document.getElementById(listStates[state]);
        div.style.display = "none";				
    }
    div = document.getElementById(id);
    if(div.style.display=="none") {
        div.style.display = "block";
    } 
}

// Allows to show and hide apps name below apps icon
function toggle_display_apps_name() {
   if(($(".behaviorName").css('display')) == 'block'){		
	    $(".behaviorName").css('display', 'none');			
	}else{													
	    $(".behaviorName").css('display', 'block');
	}
}

// Create a random id
function  make_id() {
        var id = "";
        var possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
        for( var i=0; i < 5; i++ )
            id += possible.charAt(Math.floor(Math.random() * possible.length));
        return id;
}

function make_color(){
	//To get color from the list in random order
	// var new_color = color[Math.floor(Math.random() * color.length)];
   var new_color = color[color.length-1];
   color.splice(color.indexOf(new_color),1);
   return new_color;
}

function add_app(id_div, element,lang) {
    session.service("PackageManager").then( function(pm) {
    	// Get all the information of an application
    	pm.hasPackage(element).then(function (appIsInstalled) {

    		if(appIsInstalled){

		        pm.package(element).then(function(packageInfo){
		        	session.service("AppLauncher").then( function(ap) {
		        		//Get the icon of an application
				        ap.package_icon(element).then(function (iconApp){

				        	// One application could have more than one behavior, here all behaviors are tested
				            for(i in packageInfo.behaviors){
				            	// If the user is allow by the developper of the app to launch it
				                if(packageInfo.behaviors[i].userRequestable == true){ 

				                	// Create a pseudo-random id
			                		var idElement = element+ make_id();
			                		// Counts the number of apps already added in the current tab
			                		nbBehavior = $("."+id_div).length;
				                    
				                    // If the number is even, the app will be added on the top line, else if, on the bottom line
				                    if(nbBehavior%2 == 1) {xi=2;}  else xi=1;
				                    // Add containers for app's name and app's icon
				                    $("#"+id_div+xi).append(
				                        '<div id="'+idElement+'" class="hex '+id_div+'">'+
				                        	'<img id="icon_'+idElement+'" class="iconApp" src="data:image/png;base64,'+iconApp+'"/>'+
				                            '<div id="name_'+idElement+'" class="behaviorName"></div>'+
				                        '</div>'+
				                        '<div id="zoom_'+idElement+'" class="iconApp_zoom">'+
				                        	'<img src="data:image/png;base64,'+iconApp+'"/>'+
				                        '</div>');
									///@TODO LATER: voir si on peut utiliser la même image comme zoom au lieu d'en faire 2.
									//If current language is supported in the app
				                    if(jQuery.inArray(languages[lang], packageInfo.supportedLanguages) > -1) {
				                               
				                        var runbh = element+'/'+packageInfo.behaviors[i].path;
				                        add_run_app_callback.call(this,idElement, runbh, 'animation');
				                    
				                    	//Else if behavior's name exist in current language
				                        if(packageInfo.behaviors[i].langToName[languages[lang]]){
				                        	//It is used for App's description
				                            $("#name_"+idElement).text(packageInfo.behaviors[i].langToName[languages[lang]]);
				                        }
				                        //Else if app's name exist in current language
				                        else if(packageInfo.langToName[languages[lang]]) {
				                        	//It is used for App's description
				                            $("#name_"+idElement).text(packageInfo.langToName[languages[lang]]);
				                        }
				                        //If trigger sentences exist in current language
				                        else if (packageInfo.behaviors[i].langToTriggerSentences[languages[lang]]
				                        	//and If trigger sentences are not empty in current language
				                            && packageInfo.behaviors[i].langToTriggerSentences[languages[lang]].length>0) {
				                        	//First trigger sentence is used for App's description
				                            $("#name_"+idElement).text(packageInfo.behaviors[i].langToTriggerSentences[languages[lang]][0]);
				                        }
				                    //else current language is not supported in the app
				                    }else {
				                    	//"Current language not supported" is used for App's description
				                        $("#name_"+idElement).text("#"+lang+" not supported#");

				                        //On touch, App's description is displayed below the icon app
				                        $('body').on('touchstart touchmove click', "#icon_"+idElement, function(){
				                            if (preventMultipleClick("Element")) return;
				                            $("#"+idElement).blur();
				                            audio.play();
				                                toggle_display_apps_name();  
				                        });
				                    }    
				                }
				            }
				        });     
				    }); 
		        })
			}
	    });
    });  
}

function add_app_grid(id_div, element, pm, lang){
   
	// Get all the information of an application
    pm.package(element).then(function(packageInfo){
        session.service("AppLauncher").then( function(ap) { 
        	ap.package_icon(element).then(function (iconApp){
	            // One application could have more than one behavior, here all behaviors are tested
	            for(i in packageInfo.behaviors){
	            	// If the user is allow by the developper of the app to launch it
	                if(packageInfo.behaviors[i].userRequestable == true){
	                    // Create a pseudo-random id
	                    var idElement = listTabId[i]+ make_id();
	                    // Add containers for app's name and app's icon
	                    $("#"+id_div).append(
	                    	'<div id="'+idElement+'" class="hexGrid '+id_div+'">'+
	                    		'<img id="'+idElement+'" class="gridImg" src="data:image/png;base64,'+iconApp+'"/>'+
	                    		'<div id="name_'+idElement+'" class="behaviorNameGrid"></div>'+
	                        '</div>');

	                    //If current language is supported in the app
	                    if(jQuery.inArray(languages[lang], packageInfo.supportedLanguages) > -1) {
	                               
	                        var runbh = element+'/'+packageInfo.behaviors[i].path;
	                        add_run_app_callback(idElement, runbh, 'noAnimation');
	                    
	                    	//Else if behavior's name exist in current language
	                        if(packageInfo.behaviors[i].langToName[languages[lang]]){
	                        	//It is used for App's description
	                            $("#name_"+idElement).text(packageInfo.behaviors[i].langToName[languages[lang]]);
	                        }
	                        //Else if app's name exist in current language
	                        else if(packageInfo.langToName[languages[lang]]) {
	                        	//It is used for App's description
	                            $("#name_"+idElement).text(packageInfo.langToName[languages[lang]]);
	                        }
	                        //If trigger sentences exist in current language
	                        else if (packageInfo.behaviors[i].langToTriggerSentences[languages[lang]]
	                        	//and If trigger sentences are not empty in current language
	                            && packageInfo.behaviors[i].langToTriggerSentences[languages[lang]].length>0) {
	                        	//First trigger sentence is used for App's description
	                            $("#name_"+idElement).text(packageInfo.behaviors[i].langToTriggerSentences[languages[lang]][0]);
	                        }
	                    //If current language is not supported in the app
	                    }else {
	                    	//"Current language not supported" is used for App's description
	                        $("#name_"+idElement).text("#"+lang+" not supported#");
	                    } 
	                }
	            }  
            });
        });
    });        
}

// Run application on click on the element with "idElement" as id
function add_run_app_callback(idElement, runbh, displayMethod){
     
    $('body').on('click', '#'+idElement, function(){
    	session.service("AppLauncher").then( function(ap) {
            if (preventMultipleClick("Element")) return;
            $("#"+idElement).blur();
            audio.play();

            // If the element is in one of the tabs, a zoom of the icon is played on click
            if (displayMethod == 'animation') { 
	            $(".hex").css('display', 'none');
	            var iconApp_zoom = document.getElementById("zoom_"+idElement);
	    		iconApp_zoom.style.display = "block";
            }
            ap.runBehavior(runbh).then(function() {$("#"+idElement).removeClass("btn-danger");}, function() {$("#"+idElement).addClass("btn-danger"); });
        });    
    });
}

// Add an action on click on each of those buttons
function add_settings_button(lang){

	// Go to home page
    $('#btn_home').on('touchstart touchmove click', function(){
    	if (preventMultipleClick("Element")) return;
    		audio.play();
        	show_tab('Home');
    });

    // Increase the volume
    $('#btn_volume_up').on('touchstart touchmove click', function(){
        session.service("AppLauncher").then( function(ap) {
        	if (preventMultipleClick("Element")) return;
        	audio.play();
        	ap.adjustVolume(20);
        });
    });

    // Decrease the volume
    $('#btn_volume_down').on('touchstart touchmove click', function(){
	    session.service("AppLauncher").then( function(ap) {
	        if (preventMultipleClick("Element")) return;
	        audio.play();
	        ap.adjustVolume(-20);
    	});
	});

	// Show or hide apps name below apps icon
    $('#btn_help').on('touchstart touchmove click', function(){
        if (preventMultipleClick("Element")) return;
            toggle_display_apps_name();
    });

    $('.dropdown-menu button').click(function(){
		return false;
	});
}

// If the "behaviorNameDisplayed" preference is set to "0",
function behaviorNameDisplayed_preference(){
	//  apps' name are hide, if it's set to "1", they are visible by default.
    session.service("ALPreferenceManager").then( function(pref) {
        pref.getValue("tool.applauncher", "behaviorNameDisplayed").then( function(displayed) {
            if (displayed == 1) {
            	$(".behaviorName").css('display', 'block');
            }
        });
    });
}

var delay= 3000;
// Call a methode in AppLauncher service, it allows to the service to know if the tablet is still connected.
function ping(abcd){
    console.log("start ping");
    session.service("AppLauncher").then( function(ap) {
        //delay = delay + 1;
        // "_watchTabLevel1(delay)" Methode of the sevice with the frequency of ping
        ap.ping(delay).then( function() { 
            console.log("End ping: " +delay);
        });
    });
}

$(document).ready(function(){
    
    stateChanged();

    session.then(   
        function(session) { 
            console.log('Qimessaging: connected!'); 
            ping(3000);
        },
        function() {
            console.error('Qimessaging: disconnected!');
            stateChanged();
        }
    );

    // Get the logo choosen in the preferences.
    session.service("ALPreferenceManager").then( function(pref) {
        pref.getValue("tool.applauncher", "logo").then( function(logo) {
            if (logo) {
                mainlogo = logo;
                $('#logo').css('background-image', 'url(resources/' + mainlogo + ')');
            }
        });
    });

    
    session.service("ALTextToSpeech").then( function(tts) {
        tts.getLanguage().then(function(lang) {
		    
		    // Get all the installed packages on the robot,
		    session.service("PackageManager").then(function(pm){
		    	// to add them in the grid menu	
		        pm.packages().then(function(installedApps){
		            for(var app in installedApps){
		                add_app_grid('menuApps',installedApps[app]['uuid'], pm, lang); 
		            }
		        });
		    });

        	// Add callback on settings buttons
            add_settings_button(lang);

            session.service("AppLauncher").then( function(ap) {
                console.log("Got AppLauncher");
                // Get the list of pages wrote in the preferences
                ap.get_listTab().then(function(listTabTemp){
                    listTab = listTabTemp;
                    for (id in listTab){
                        if (id == 0){
                        	// Add "Home" as id for the home page
                            listTabId.push('Home');
                            ///@TODO: voir si l'id de la page peut venir du python #futureproof
                        // Make a unique id for each page
                        }else listTabId.push(make_id()); 			
                    }
                    // Add div container for each page
                    add_div_tab(listTabId);
                    // Get the list of apps wrote in the preferences
                    ap.get_listApp().then(function(listAppTemp){
                        listApp = listAppTemp;
                        
                        // For each page
                        for (var pageId in listTabId){
                            if(pageId == 0){
                            	// Add the buttons to the home page with names of pages according to robot preferences
                                add_button_home_page(listTabId[pageId]);
                            }else{
                            	// For each app according to a page
                                for (var currentApp in listApp[pageId]){
                                    add_app(listTabId[pageId], listApp[pageId][currentApp], lang);
                                } 
                            } 
                        }
                        // Display home page
                        show_tab('Home');
                        // Display or not apps' names according to robot preference
                        setTimeout(behaviorNameDisplayed_preference,3000);
                    });
                });
                // Each time, python service AppLauncher require a ping, function "ping" in javascript is called
                ap.ping_required.connect(ping);
                // Get the value of robot current state
                ap.current_state.value().then( stateChanged, function(error) { console.log(error); display_window(".main_menu");  });
                // Each time robot current state changed, function "stateChanged" is called
                ap.current_state.connect(stateChanged);
                
            }, function(error) {console.log("Got error: ", error);});
        });
    });    
});