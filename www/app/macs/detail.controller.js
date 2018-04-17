angular
	.module("macmonApp")
	.controller("Macs.DetailController", Controller);

function Controller($http, $stateParams) {

	var vm = this;
	vm.saveMac = saveMac;
	vm.loading = false;
	vm.submitted = false;

	initController();

	function initController() {

		$http.get(`/macs?id=eq.${$stateParams.macId}`).then(
			function (res) {
				// console.log(res);
				vm.item = res.data[0];
			},
			function (err) {
				console.log(err);
			}
		);

	};

	function saveMac() {
		
		vm.loading = true;

		var data = {
 			// confirmed: vm.item.confirmed,
 			desc: vm.item.desc,
 		};

 		$http.patch(`/macs?id=eq.${$stateParams.macId}`, data).then(
 			function(res) {
 				console.log(res);
 				vm.loading = false;
 				vm.submitted = true;
 			},
 			function(err) {
 				console.log(err);
 			}
 		);

	};

};