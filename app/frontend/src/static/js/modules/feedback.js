// src/static/js/modules/feedback.js

/**
 * Feedback Module - Handles feedback form interactions and submission.
 */

export function setupFeedback() {
    const btn = document.getElementById('feedback-btn');
    const modal = document.getElementById('feedback-modal');
    const closeBtn = document.getElementById('feedback-close');
    const form = document.getElementById('feedback-form');
    const thankYou = document.getElementById('feedback-thankyou');
    const submitBtn = form ? form.querySelector('.feedback-submit') : null;
    const sliders = form ? form.querySelectorAll('.rating-slider') : [];

    if (!btn || !modal || !closeBtn || !form) {
        return;
    }

    function toggleModal() {
        if (modal.style.display === 'block') {
            modal.style.display = 'none';
            form.style.display = 'block';
            if (thankYou) thankYou.style.display = 'none';
            form.reset();
            updateSubmitState();
        } else {
            modal.style.display = 'block';
        }
    }

    btn.addEventListener('click', toggleModal);
    closeBtn.addEventListener('click', toggleModal);

    sliders.forEach(slider => {
        const bubble = document.createElement('div');
        bubble.className = 'slider-bubble';
        slider.parentElement.appendChild(bubble);

        function positionBubble() {
            const val = slider.value;
            const min = parseFloat(slider.min || 0);
            const max = parseFloat(slider.max || 100);
            const percent = (val - min) / (max - min);
            const sliderWidth = slider.offsetWidth;
            bubble.textContent = val;
            bubble.style.left = `${percent * sliderWidth}px`;
        }

        slider.addEventListener('input', () => {
            bubble.style.display = 'block';
            positionBubble();
        });
        slider.addEventListener('change', () => {
            bubble.style.display = 'none';
        });
        slider.addEventListener('focus', () => {
            bubble.style.display = 'block';
            positionBubble();
        });
        slider.addEventListener('blur', () => {
            bubble.style.display = 'none';
        });

        positionBubble();
    });

    function updateSubmitState() {
        if (!submitBtn) return;
        let complete = true;
        for (let i = 1; i <= 10; i++) {
            const input = form.querySelector(`input[name="q${i}"]`);
            if (!input || input.value === '') {
                complete = false;
                break;
            }
        }
        submitBtn.disabled = !complete;
    }

    form.addEventListener('input', updateSubmitState);
    updateSubmitState();

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        updateSubmitState();
        if (submitBtn && submitBtn.disabled) {
            return;
        }
        const ratings = [];
        for (let i = 1; i <= 10; i++) {
            const val = parseInt(form[`q${i}`].value, 10);
            ratings.push(val);
        }
        const comments = form['comments'].value;

        fetch(`${window.BACKEND_URL}/feedback`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ratings, comments, userToken: `${window.USER_TOKEN}`})
        }).then(() => {
            form.style.display = 'none';
            if (thankYou) thankYou.style.display = 'block';
        }).catch(err => {
            console.error('Feedback submission failed:', err);
        });
    });
}
