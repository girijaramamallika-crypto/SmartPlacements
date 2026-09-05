(() => {
    const heroCarousel = document.querySelector("#homeHeroCarousel");
    if (heroCarousel) {
        const slides = heroCarousel.querySelectorAll(".carousel-item");
        let activeSlide = 0;
        window.setInterval(() => {
            slides[activeSlide].classList.remove("active");
            activeSlide = (activeSlide + 1) % slides.length;
            slides[activeSlide].classList.add("active");
        }, 1500);
    }

    document.querySelectorAll("form").forEach((form) => {
        form.querySelectorAll("input, textarea, select").forEach((field) => {
            field.addEventListener("input", () => {
                field.classList.remove("is-invalid");
            });
        });

        form.addEventListener("submit", (event) => {
            let firstInvalid = null;
            form.querySelectorAll("input, textarea, select").forEach((field) => {
                if (field.type === "hidden" || field.disabled) return;
                const valid = field.checkValidity();
                field.classList.toggle("is-invalid", !valid);
                if (!valid && !firstInvalid) firstInvalid = field;
            });
            if (firstInvalid) {
                event.preventDefault();
                firstInvalid.focus();
            }
        });
    });
})();
