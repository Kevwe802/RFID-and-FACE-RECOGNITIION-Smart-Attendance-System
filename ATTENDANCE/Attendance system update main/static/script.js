// Add any JavaScript for dynamic interactions, such as sorting columns or filtering data

// Example: Highlight a row when clicked
document.addEventListener('DOMContentLoaded', () => {
    const rows = document.querySelectorAll('.styled-table tbody tr');
    rows.forEach(row => {
        row.addEventListener('click', () => {
            rows.forEach(r => r.classList.remove('active-row'));
            row.classList.add('active-row');
        });
    });
});
