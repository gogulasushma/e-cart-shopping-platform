document.addEventListener("DOMContentLoaded", function () {
    const checkoutForm = document.getElementById("checkout-form");
    const confirmButton = document.getElementById("confirm-button");

    // Avoid accidental double submission of the checkout form.
    if (checkoutForm && confirmButton) {
        checkoutForm.addEventListener("submit", function () {
            confirmButton.disabled = true;
            confirmButton.textContent = "Placing your order...";
        });
    }

    // Automatically dismiss success/error alerts after a short delay.
    document.querySelectorAll(".alert").forEach(function (alertBox) {
        window.setTimeout(function () {
            if (alertBox && alertBox.parentNode) {
                alertBox.classList.remove("show");
                window.setTimeout(function () {
                    if (alertBox.parentNode) alertBox.remove();
                }, 250);
            }
        }, 4500);
    });
});
