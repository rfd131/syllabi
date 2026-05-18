/**
 * Navigation for Math 486 syllabus.
 *
 * Math 486 is asynchronous online with a single instructor and traditional
 * points-based grading, so the nav is much simpler than the 140B/141B
 * mastery-grading version this is modeled on.
 */

const navigationData = {
    topNav: [
        { title: "Home", href: "index.html" },
        { title: "Instructor", href: "instructors.html" },
        {
            title: "Schedule",
            href: "schedule.html",
            dropdown: [
                { title: "Lessons 1–7 (Non-cooperative)", href: "schedule.html#non-cooperative" },
                { title: "Lessons 8–10 (Evolutionary)", href: "schedule.html#evolutionary" },
                { title: "Exams", href: "schedule.html#exams" }
            ]
        },
        {
            title: "Materials",
            href: "materials.html",
            dropdown: [
                { title: "Required Textbook", href: "materials.html#textbook" },
                { title: "Optional Resources", href: "materials.html#optional" },
                { title: "Course Tools", href: "materials.html#tools" }
            ]
        },
        {
            title: "Grading",
            href: "grading.html",
            dropdown: [
                { title: "Overview", href: "grading.html#overview" },
                { title: "Point Distribution", href: "grading.html#points" },
                { title: "Letter Grades", href: "grading.html#letter-grades" },
                { title: "Homework Revisions & Exceptions", href: "grading.html#revisions" }
            ]
        },
        {
            title: "Policies",
            href: "policies.html",
            dropdown: [
                { title: "Late Work", href: "policies.html#late-work" },
                { title: "Academic Integrity", href: "policies.html#academic-integrity" },
                { title: "Generative AI", href: "policies.html#ai-policy" },
                { title: "Nondiscrimination", href: "policies.html#nondiscrimination" },
                { title: "Disability Accommodation", href: "policies.html#disability" }
            ]
        },
        {
            title: "Getting Help",
            href: "help.html",
            dropdown: [
                { title: "Office Hours", href: "help.html#office-hours" },
                { title: "Piazza", href: "help.html#piazza" },
                { title: "Penn State Learning", href: "help.html#tutoring" }
            ]
        },
        {
            title: "Student Resources",
            href: "resources.html",
            dropdown: [
                { title: "Counseling Services", href: "resources.html#counseling" },
                { title: "Educational Equity", href: "resources.html#equity" },
                { title: "Disability Resources", href: "resources.html#disability" }
            ]
        }
    ],
    sidebarNav: [
        { title: "Welcome & Overview", href: "index.html" },
        { title: "Instructor", href: "instructors.html" },
        { title: "Schedule", href: "schedule.html" },
        { title: "Materials", href: "materials.html" },
        { title: "Grading", href: "grading.html" },
        { title: "Policies", href: "policies.html" },
        { title: "Getting Help", href: "help.html" },
        { title: "Student Resources", href: "resources.html" }
    ],
    quickLinks: [
        { icon: "🔑", title: "Math 486 Webapp", href: "webapp.html" },
        { icon: "📅", title: "Schedule of Topics", href: "schedule.html" },
        { icon: "📊", title: "How Your Grade is Determined", href: "grading.html" },
        { icon: "📝", title: "Late Work & Exceptions", href: "policies.html#late-work" },
        { icon: "🤖", title: "Generative AI Policy", href: "policies.html#ai-policy" },
        { icon: "🕐", title: "Office Hours", href: "help.html#office-hours" }
    ],
    importantDates: [
        "Term: May 18 – Aug 14, 2026",
        "Midterm: Week 7 (exact dates TBD)",
        "Late Drop: Friday, July 24 (11:59 PM ET)",
        "Final (take-home): Week 12 (exact dates TBD)",
        "Final (in-person): TBD (Wed Aug 12 – Fri Aug 14)"
    ]
};


function generateTopNav(currentPage = '') {
    let html = `
    <nav>
        <div class="nav-container">
            <ul class="nav-links">`;

    navigationData.topNav.forEach(item => {
        const isCurrentPage = item.href === currentPage;
        html += `
                <li class="nav-item${isCurrentPage ? ' current-page' : ''}">
                    <a href="${item.href}">${item.title}`;

        if (item.dropdown && item.dropdown.length > 0) {
            html += ` <span class="dropdown-arrow">▼</span></a>
                    <div class="dropdown-menu">`;
            item.dropdown.forEach(subItem => {
                html += `
                        <a href="${subItem.href}">${subItem.title}</a>`;
            });
            html += `
                    </div>`;
        } else {
            html += `</a>`;
        }
        html += `
                </li>`;
    });

    html += `
            </ul>
        </div>
    </nav>`;

    return html;
}


function generateSidebarNav(currentPage = '') {
    let html = `
        <style>
            :root {
                --penn-state-blue: #001e44;
                --penn-state-navy: #041e42;
                --light-gray: #f5f5f5;
                --white: #ffffff;
            }
            .sidebar-navigation {
                width: 280px;
                background-color: var(--light-gray);
                padding: 2rem 1rem;
                position: sticky;
                top: 80px;
                height: calc(100vh - 80px);
                overflow-y: auto;
                border-right: 2px solid var(--penn-state-blue);
                z-index: 1;
            }
            .sidebar-navigation h2 {
                font-size: 1.1rem;
                color: var(--penn-state-navy);
                margin-bottom: 1rem;
                padding-bottom: 0.5rem;
                border-bottom: 2px solid var(--penn-state-blue);
            }
            .sidebar-navigation ul { list-style: none; margin: 0; padding: 0; }
            .sidebar-navigation .nav-item { position: relative; margin-bottom: 0.25rem; }
            .sidebar-navigation .nav-item > a {
                color: var(--penn-state-blue);
                text-decoration: none;
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 0.5rem;
                border-radius: 4px;
                transition: background-color 0.3s ease;
                font-weight: 500;
                font-size: 0.95rem;
            }
            .sidebar-navigation .nav-item > a:hover,
            .sidebar-navigation .nav-item > a:focus {
                background-color: var(--white);
                text-decoration: underline;
                outline: 2px solid var(--penn-state-blue);
                outline-offset: 2px;
            }
            .sidebar-navigation .nav-item.current-page > a {
                background-color: var(--penn-state-blue);
                color: var(--white);
            }
            .sidebar-navigation .dropdown-arrow {
                font-size: 0.8em;
                transition: transform 0.3s ease;
            }
            .sidebar-navigation .nav-item.active .dropdown-arrow {
                transform: rotate(180deg);
            }
            .sidebar-navigation .dropdown-menu {
                display: none;
                background-color: var(--white);
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-top: 4px;
                position: static;
                margin-left: 0.5rem;
                margin-top: 0.25rem;
                box-shadow: inset 0 0 4px rgba(0,0,0,0.1);
                z-index: 1000;
            }
            .sidebar-navigation .nav-item.active .dropdown-menu { display: block; }
            .sidebar-navigation .dropdown-menu a {
                display: block;
                padding: 0.5rem 1rem;
                color: #666;
                text-decoration: none;
                font-size: 0.9rem;
                transition: background-color 0.3s ease;
            }
            .sidebar-navigation .dropdown-menu a:hover { background-color: var(--light-gray); }
        </style>
        <nav class="sidebar-navigation" role="navigation" aria-label="Syllabus sections">
            <h2>Syllabus Sections</h2>
            <ul>`;

    navigationData.sidebarNav.forEach(item => {
        const isCurrentPage = item.href === currentPage;
        const topNavItem = navigationData.topNav.find(navItem => navItem.href === item.href);
        const hasDropdown = topNavItem && topNavItem.dropdown;

        html += `
                <li class="nav-item${isCurrentPage ? ' current-page' : ''}">
                    <a href="${item.href}">${item.title}${hasDropdown ? ' <span class="dropdown-arrow">▼</span>' : ''}</a>`;

        if (hasDropdown) {
            html += `
                    <div class="dropdown-menu">`;
            topNavItem.dropdown.forEach(subItem => {
                html += `
                        <a href="${subItem.href}">${subItem.title}</a>`;
            });
            html += `
                    </div>`;
        }

        html += `
                </li>`;
    });

    html += `
            </ul>
        </nav>`;

    return html;
}


function generateQuickLinks() {
    let html = `
    <aside class="quick-links" role="complementary" aria-label="Quick Links">
        <h2>Quick Links</h2>
        <ul>`;

    navigationData.quickLinks.forEach(link => {
        const external = link.external ? ' target="_blank" rel="noopener noreferrer"' : '';
        html += `
            <li>
                <a href="${link.href}"${external}>
                    <span class="icon">${link.icon}</span>
                    ${link.title}
                </a>
            </li>`;
    });

    html += `
        </ul>

        <div class="important-dates-box">
            <h3>Important Dates</h3>
            <ul>`;

    navigationData.importantDates.forEach(date => {
        html += `
                <li>${date}</li>`;
    });

    html += `
            </ul>
        </div>
    </aside>`;

    return html;
}


function initializeNavigation(currentPage = '') {
    if (!currentPage) {
        const path = window.location.pathname;
        currentPage = path.substring(path.lastIndexOf('/') + 1) || 'index.html';
    }

    const topNavContainer = document.getElementById('top-navigation');
    if (topNavContainer) topNavContainer.innerHTML = generateTopNav(currentPage);

    const sidebarContainer = document.getElementById('sidebar-navigation');
    if (sidebarContainer) sidebarContainer.innerHTML = generateSidebarNav(currentPage);

    const quickLinksContainer = document.getElementById('quick-links-sidebar');
    if (quickLinksContainer) quickLinksContainer.innerHTML = generateQuickLinks();
}


if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        generateTopNav,
        generateSidebarNav,
        generateQuickLinks,
        initializeNavigation,
        navigationData
    };
}
