var haslocalStorage = (function() {
	var mod = 'modernizr';
	try {
		localStorage.setItem(mod, mod);
		localStorage.removeItem(mod);
		return true;
	} catch(e) {
		return false;
	}
})();

$(document).ready(function() {
	$(".button-collapse").sideNav({'edge': 'left'});

	if (haslocalStorage) {
		if (localStorage.getItem("debug") === "on") {
			$(".debugbutton").show();
			$(".debug").show();
		}
	}

	$(".post img").addClass("responsive-img");
});
