// Ensure GSAP and ScrollTrigger are included
gsap.registerPlugin(ScrollTrigger);

// Hero Section Animation
gsap.from(".hero-content h1", {
    duration: 1.5,
    y: -100,
    opacity: 0,
    ease: "power3.out",
    delay: 0.5
});

gsap.from(".hero-content p", {
    duration: 1.5,
    y: 100,
    opacity: 0,
    ease: "power3.out",
    delay: 1
});

// Scroll-triggered animations for hero section
gsap.to(".hero-content h1", {
    scrollTrigger: {
        trigger: ".hero",
        start: "top top",
        end: "bottom top",
        scrub: true,
        toggleActions: "play reverse play reverse",
        markers: false
    },
    x: -window.innerWidth,
});

gsap.to(".line", {
    scrollTrigger: {
        trigger: ".hero",
        start: "top top",
        end: "bottom top",
        scrub: true,
        toggleActions: "play reverse play reverse",
        markers: false
    },
    scaleX: 0,
});

gsap.to(".hero-content p", {
    scrollTrigger: {
        trigger: ".hero",
        start: "top top",
        end: "bottom top",
        scrub: true,
        toggleActions: "play reverse play reverse",
        markers: false
    },
    x: window.innerWidth,
});

// Interactive Portfolio Gallery
gsap.from(".portfolio-item", {
    duration: 1.2,
    scale: 0.9,
    opacity: 0,
    stagger: 0.3,
    ease: "power3.out"
});
function openModal(quoteId) {
    fetch(`/quote_details/${quoteId}`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('quote_id').value = data.id;
            document.getElementById('quoteDetails').innerHTML = `
                <p><strong>Business Type:</strong> ${data.business_type}</p>
                <p><strong>Requirements:</strong> ${data.requirements}</p>
                <p><strong>Contact Info:</strong> ${data.contact_info}</p>
                <p><strong>Status:</strong> <select name="status">
                    <option value="Pending" ${data.status === 'Pending' ? 'selected' : ''}>Pending</option>
                    <option value="Accepted" ${data.status === 'Accepted' ? 'selected' : ''}>Accepted</option>
                    <option value="Denied" ${data.status === 'Denied' ? 'selected' : ''}>Denied</option>
                </select></p>
                <p><strong>Quote Price:</strong> <input type="number" step="0.01" name="quote_price" value="${data.quote_price || ''}"></p>
            `;
            document.getElementById('quoteModal').style.display = 'flex';
        });
}

function openRequestModal() {
    document.getElementById('requestModal').style.display = 'flex';
}

function closeQuoteModal() {
    document.getElementById('quoteModal').style.display = 'none';
}

function closeRequestModal() {
    document.getElementById('requestModal').style.display = 'none';
}

function openUpdatesModal() {
    fetch('/get_updates')
        .then(response => response.json())
        .then(data => {
            let updatesHtml = '';
            data.forEach(update => {
                updatesHtml += `<div class="update-item">
                    <p><strong>${update.timestamp}:</strong> ${update.content}</p>
                </div>`;
            });
            document.getElementById('updatesList').innerHTML = updatesHtml;
            document.getElementById('updatesModal').style.display = 'flex';
        });
}

function closeUpdatesModal() {
    document.getElementById('updatesModal').style.display = 'none';
}

// Close the modals when clicking outside of them
window.onclick = function(event) {
    if (event.target === document.getElementById('quoteModal')) {
        closeQuoteModal();
    }
    if (event.target === document.getElementById('requestModal')) {
        closeRequestModal();
    }
    if (event.target === document.getElementById('updatesModal')) {
        closeUpdatesModal();
    }
}

    // Function to add animation class when section comes into view
    function handleScroll() {
        const separator = document.querySelector('.section-separator');
        const sectionPosition = separator.getBoundingClientRect().top;
        const viewportHeight = window.innerHeight;

        if (sectionPosition < viewportHeight) {
            separator.classList.add('animate');
        } else {
            separator.classList.remove('animate');
        }
    }

    // Add scroll event listener
    window.addEventListener('scroll', handleScroll);

    // Initial check
    handleScroll();
