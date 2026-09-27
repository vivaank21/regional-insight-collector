/**
 * script.js
 * ----------
 * GSAP-driven animations for the Regional Insight Collector.
 * No external tracking, no analytics — purely presentational.
 */

document.addEventListener("DOMContentLoaded", () => {
    const page = document.body.dataset.page || "landing";

    if (page === "experience") {
        initExperiencePage();
    } else {
        initLandingPage();
    }
});

/* ------------------------------------------------------------------
   Landing page
   ------------------------------------------------------------------ */

function initLandingPage() {
    if (typeof gsap === "undefined") return;

    const tl = gsap.timeline({ defaults: { ease: "power3.out" } });

    // Ambient background settles in first.
    tl.from(".glow-orb", { opacity: 0, scale: 0.7, duration: 1.2 })
      .from(".grid-mesh", { opacity: 0, duration: 1.4 }, "<");

    // Heading lines rise into place.
    tl.from(".landing-heading .line", {
        yPercent: 110,
        opacity: 0,
        duration: 0.9,
        stagger: 0.12,
    }, "-=0.8");

    // Supporting copy and form fade/slide up together.
    tl.from(
        [".eyebrow-mark", ".landing-subtitle", ".discover-form", ".privacy-note"],
        { y: 24, opacity: 0, duration: 0.7, stagger: 0.08 },
        "-=0.5"
    );

    // Globe visual arrives with a soft scale + fade.
    tl.from(".globe-stage", { opacity: 0, scale: 0.85, duration: 1 }, "-=0.9");

    // Slow continuous rotation for the ring group (subtle, non-distracting).
    gsap.to("#globeRings", {
        rotate: 360,
        transformOrigin: "200px 200px",
        duration: 60,
        repeat: -1,
        ease: "none",
    });

    // Gentle pulse on the location pin, like a satellite lock acquiring.
    gsap.timeline({ repeat: -1 })
        .to(".pin-pulse", { opacity: 0.8, scale: 1, duration: 0.1 })
        .to(".pin-pulse", { opacity: 0, scale: 2.4, duration: 1.4, ease: "power1.out" })
        .to({}, { duration: 0.8 }); // pause between pulses

    initCtaHover();
    initFormSubmit();
}

function initCtaHover() {
    const btn = document.getElementById("discoverBtn");
    const arrow = btn ? btn.querySelector(".btn-arrow") : null;
    if (!btn) return;

    btn.addEventListener("mouseenter", () => {
        gsap.to(btn, { scale: 1.03, boxShadow: "0 16px 36px -8px rgba(79,140,255,0.65)", duration: 0.25, ease: "power2.out" });
        if (arrow) gsap.to(arrow, { x: 4, duration: 0.25, ease: "power2.out" });
    });

    btn.addEventListener("mouseleave", () => {
        gsap.to(btn, { scale: 1, boxShadow: "0 12px 30px -10px rgba(79,140,255,0.55)", duration: 0.25, ease: "power2.out" });
        if (arrow) gsap.to(arrow, { x: 0, duration: 0.25, ease: "power2.out" });
    });
}

function initFormSubmit() {
    const form = document.getElementById("discoverForm");
    const overlay = document.getElementById("loadingOverlay");
    if (!form || !overlay) return;

    form.addEventListener("submit", (event) => {
        const input = document.getElementById("user_name");
        if (input && !input.value.trim()) {
            // Let native/server-side validation handle the empty case;
            // don't show the loading state for an obviously-empty submit.
            return;
        }

        // Show the polished, non-technical loading state while the
        // server resolves the visitor's regional experience.
        overlay.classList.add("is-active");
        gsap.fromTo(
            overlay,
            { opacity: 0 },
            { opacity: 1, duration: 0.35, ease: "power1.out" }
        );
        gsap.fromTo(
            ".loading-ring, .loading-text",
            { y: 12, opacity: 0 },
            { y: 0, opacity: 1, duration: 0.4, delay: 0.1, stagger: 0.05 }
        );
        // Form submits normally (standard POST); the overlay simply
        // covers the brief network round-trip.
    });
}

/* ------------------------------------------------------------------
   Experience page
   ------------------------------------------------------------------ */

function initExperiencePage() {
    if (typeof gsap === "undefined") return;

    const tl = gsap.timeline({ defaults: { ease: "power3.out" } });

    tl.from(".glow-orb", { opacity: 0, scale: 0.7, duration: 1.1 })
      .from(".experience-eyebrow", { y: -16, opacity: 0, duration: 0.6 }, "-=0.7")
      .from(".experience-card", { y: 30, opacity: 0, duration: 0.8 }, "-=0.3")
      .from("#regionalImage", { opacity: 0, scale: 1.08, duration: 1.1 }, "-=0.6")
      .from(
          ["#welcomeHeading", ".location-line", "#experienceTagline", "#returnBtn"],
          { y: 18, opacity: 0, duration: 0.6, stagger: 0.08 },
          "-=0.7"
      );
}
