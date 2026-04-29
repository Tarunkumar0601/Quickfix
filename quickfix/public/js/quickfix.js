$(document).ready(() => {
	const shopname = frappe.boot.quickfix_shop_name;

	if (shopname) {
		setTimeout(() => {
			const navbarBrand = document.querySelector(".navbar-home");
			if (navbarBrand) {
				navbarBrand.innerHTML = `
                <span style="font-weight:600; color:#2c3e50;">
                ${shopname}
                </span>
                `;
			}
		}, 500);
	}
});
