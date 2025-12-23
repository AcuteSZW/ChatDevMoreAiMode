'''
This script is responsible for displaying "helloworld" on the webpage.
'''
// This script is responsible for displaying "helloworld" on the webpage.
document.addEventListener('DOMContentLoaded', function() {
    const contentDiv = document.getElementById('content');
    contentDiv.textContent = 'helloworld';
});