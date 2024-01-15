/*
    Core logic/payment flow for this comes from here:
    https://stripe.com/docs/payments/accept-a-payment
    https://stripe.com/docs/payments/accept-a-payment?platform=web&ui=elements

    CSS from here: 
    https://stripe.com/docs/stripe-js
    https://stripe.com/docs/js/appendix/style?type=card#appendix-style-type-card
*/

var stripePublicKey = $("#id_stripe_public_key").text().slice(1, -1);
var clientSecret = $("#id_client_secret").text().slice(1, -1);
var stripe = Stripe(stripePublicKey);
var elements = stripe.elements();
var style = {
	// Style the card Element with the default style from old stripe docs not available in new docs
	base: {
		color: "#000",
		fontFamily: '"Helvetica Neue", Helvetica, sans-serif',
		fontSmoothing: "antialiased",
		fontSize: "16px",
		"::placeholder": {
			color: "#aab7c4",
		},
	},
	invalid: {
		color: "#dc3545",
		iconColor: "#dc3545",
	},
};
var card = elements.create("card", { style: style }); // Create an instance of the card Element
card.mount("#card-element");

// Handle realtime validation errors on the card Element
card.addEventListener("change", function (event) {
	var errorDiv = document.getElementById("card-errors"); // Get the error div
	if (event.error) {
		// If there is an error, show it in the card error div
		var html = `
			<span class="icon" role="alert">
				<i class="fas fa-times"></i>
			</span>
			<span>${event.error.message}</span> 
		`;
		$(errorDiv).html(html); // Add the error message to the error div
	} else {
		errorDiv.textContent = ""; // Clear the error div if there are no errors
	}
});

// Payment Intent is no longer used in Stripe as they use Payment elements instead
// PaymentIntent steps are as follows:
// 1. Checkout view creates a Stripe PaymentIntent on the server
// 2. Stripe returns client_secret, which we return to the template
// 3. Use the client_secret in the template to call confirmCardPayment() and verify the card

// Handle form submit
var form = document.getElementById("payment-form"); // Get the payment form

form.addEventListener("submit", function (ev) {
	ev.preventDefault(); // Prevent the form from submitting
	card.update({ disabled: true });
	$("#submit-button").attr("disabled", true); // Disable the card element and submit button to prevent multiple submissions
	$("#payment-form").fadeToggle(100); // Fade out the form
	$("#loading-overlay").fadeToggle(100); // Fade in the loading overlay
	stripe
		.confirmCardPayment(clientSecret, {
			payment_method: {
				card: card, // Pass the card Element to confirmCardPayment
			},
		}) // If the card is valid, confirm the payment
		.then(function (result) {
			if (result.error) {
				// Show error to your customer (e.g., insufficient funds)
				var errorDiv = document.getElementById("card-errors");
				var html = `
                <span class="icon" role="alert">
                <i class="fas fa-times"></i>
                </span>
                <span>${result.error.message}</span>`;
				$(errorDiv).html(html);
				$("#payment-form").fadeToggle(100); // Re-show the form
				$("#loading-overlay").fadeToggle(100); // Hide the loading overlay
				// Re-enable the card Element and submit button if there is an error to allow the user to fix it
				card.update({ disabled: false });
				$("#submit-button").attr("disabled", false);
			} else {
				// The payment has been processed and will submit the form
				if (result.paymentIntent.status === "succeeded") {
					form.submit();
				}
			}
		});
});