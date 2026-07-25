// Hide the success message automatically after 4 seconds
document.addEventListener('DOMContentLoaded', function () {
    setTimeout(function () {
        const alerts = document.querySelectorAll('.alert-success');
        alerts.forEach(function (alert) {
            alert.classList.remove('show');
        });
    }, 4000);
});
