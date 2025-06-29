// static/js/script.js

// Kamu bisa menambahkan JavaScript di sini untuk interaktivitas
// seperti validasi form, efek loading, atau animasi.

// Contoh sederhana: alert saat halaman dimuat
// window.onload = function() {
//     console.log("FoodCourt app loaded!");
// };

// Contoh: Menggulir ke atas saat ada pesan flash
document.addEventListener('DOMContentLoaded', function() {
    const flashes = document.querySelector('.flashes');
    if (flashes && flashes.children.length > 0) {
        window.scrollTo(0, 0); // Gulir ke paling atas untuk melihat pesan
    }
});

// Contoh: Membuat input quantity tidak kurang dari 1 (sudah ada di HTML dengan min="1")
// document.querySelectorAll('input[type="number"]').forEach(input => {
//     input.addEventListener('change', function() {
//         if (this.value < 1) {
//             this.value = 1;
//         }
//     });
// });