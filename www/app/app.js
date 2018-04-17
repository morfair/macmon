
var macmonApp = angular.module("macmonApp", [
		"ui.router",
		"ui.bootstrap",
		"ngAnimate",
		"ngTouch",
		"ngStorage",
		"smart-table",
		// "xeditable",
	])
	.config(config)
	.run(run);


function config($stateProvider, $urlRouterProvider, $provide, $httpProvider) {

	$urlRouterProvider.otherwise("/");

	$stateProvider
		.state("login", {
			url: "/login",
			templateUrl:"app/login/index.view.html",
			controller: "Login.IndexController",
			controllerAs: "vm",
		})
		
		.state("maclist", {
			url: "/",
			templateUrl: "app/macs/index.view.html",
			controller: "Macs.IndexController",
			controllerAs: "vm",
		})
		.state("macdetail", {
			url: "/mac/:macId",
			templateUrl: "app/macs/detail.view.html",
			controller: "Macs.DetailController",
			controllerAs: "vm",
		})

		.state("about", {
			url: '/about',
			template: '<h3>Its the UI-Router hello world app!</h3>'
		})


		$provide.factory('myHttpInterceptors', function ($q, $injector) {
	        return {

	        	// "success": function(res) {
	        	// 	return res;
	        	// },

	            "responseError": function(err) {
	                console.log($injector);
	                if (err.status === 401) {
	                    $injector.get('$state').go('login');
	                }
	 
	                return $q.reject(err);
	            },

	        };
	    });
	 
	    $httpProvider.interceptors.push('myHttpInterceptors');

};


function run($rootScope, $http, $location, $localStorage) {

	// keep user logged in after page refresh
	if ($localStorage.currentUser) {
		$http.defaults.headers.common.Authorization = 'Bearer ' + $localStorage.currentUser.token;
	}

	// redirect to login page if not logged in and trying to access a restricted page
	$rootScope.$on('$locationChangeStart', function (event, next, current) {
		var publicPages = ['/login'];
		var restrictedPage = publicPages.indexOf($location.path()) === -1;
		if (restrictedPage && !$localStorage.currentUser) {
			$location.path('/login');
		}
	});


	// https://vitalets.github.io/angular-xeditable/#getstarted
	// bootstrap3 theme. Can be also 'bs2', 'default'
	// https://vitalets.github.io/angular-xeditable/#default
	// editableOptions.theme = 'bs3';
	// editableOptions.icon = "font-awesome";

}

