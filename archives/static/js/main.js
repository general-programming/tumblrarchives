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
		if (localStorage.getItem("debug") !== null) {
			$(".debugbutton").show();
			$(".debug").show();
		}
	}

	$(".post img").addClass("responsive-img");

	hljs.initHighlightingOnLoad();
});

function init_graph(data) {
	var container = document.getElementById("graph");

	var parsed = {
	  nodes: new vis.DataSet(data.nodes),
	  edges: new vis.DataSet(data.edges)
	};

	var options = {
	  "layout": {
	    "improvedLayout": false
	  },
	  "edges": {
	    "smooth": false,
			"hidden": true
	  },
	  "physics": {
	    "repulsion": {
	      "centralGravity": 0.1,
	      "springLength": 100,
	      "nodeDistance": 750
	    },
	    "minVelocity": 0.75,
	    "solver": "repulsion",
	    "timestep": 0.15
	  }
	}

	// initialize your network!
	var network = new vis.Network(container, parsed, options);

	network.on("doubleClick", function (params) {
	  var node = parsed.nodes.get(params["nodes"][0]);
	  var url = node.label;
	  window.open("http://" + url + ".tumblr.com");
	});
}