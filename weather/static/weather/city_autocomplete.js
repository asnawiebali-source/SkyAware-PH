
/*
 * SkyAware PH - Philippine City Autocomplete
 *
 * Used for standard city search forms, including:
 * - Weather Forecast
 * - Air Quality
 * - Homepage city search
 *
 * IMPORTANT:
 * The Dashboard has its own autocomplete that
 * combines saved locations and local cities.
 * This script deliberately skips that input.
 *
 * Suggestions use local data only.
 * Nominatim is called by Django after submission.
 */

(function () {
    "use strict";

    // =========================================
    // LOCAL PHILIPPINE CITIES AND TOWNS
    // =========================================

    const LOCAL_CITIES = [

        // Northern Mindanao
        ["Iligan City", "Lanao del Norte"],
        ["Cagayan de Oro", "Misamis Oriental"],
        ["Marawi City", "Lanao del Sur"],
        ["Ozamiz City", "Misamis Occidental"],
        ["Oroquieta City", "Misamis Occidental"],
        ["Tangub City", "Misamis Occidental"],
        ["Malaybalay City", "Bukidnon"],
        ["Valencia City", "Bukidnon"],
        ["Gingoog City", "Misamis Oriental"],
        ["El Salvador City", "Misamis Oriental"],
        ["Lugait", "Misamis Oriental"],
        ["Manticao", "Misamis Oriental"],
        ["Naawan", "Misamis Oriental"],
        ["Initao", "Misamis Oriental"],
        ["Opol", "Misamis Oriental"],
        ["Jasaan", "Misamis Oriental"],
        ["Linamon", "Lanao del Norte"],
        ["Kauswagan", "Lanao del Norte"],
        ["Kolambugan", "Lanao del Norte"],
        ["Tubod", "Lanao del Norte"],

        // Caraga
        ["Butuan City", "Agusan del Norte"],
        ["Surigao City", "Surigao del Norte"],
        ["Tandag City", "Surigao del Sur"],
        ["Bislig City", "Surigao del Sur"],
        ["Bayugan City", "Agusan del Sur"],
        ["Cabadbaran City", "Agusan del Norte"],

        // Davao Region
        ["Davao City", "Davao del Sur"],
        ["Tagum City", "Davao del Norte"],
        ["Panabo City", "Davao del Norte"],
        ["Digos City", "Davao del Sur"],
        ["Mati City", "Davao Oriental"],
        ["Samal City", "Davao del Norte"],

        // SOCCSKSARGEN
        ["General Santos City", "South Cotabato"],
        ["Koronadal City", "South Cotabato"],
        ["Kidapawan City", "Cotabato"],
        ["Tacurong City", "Sultan Kudarat"],

        // Zamboanga Peninsula
        ["Zamboanga City", "Zamboanga del Sur"],
        ["Pagadian City", "Zamboanga del Sur"],
        ["Dipolog City", "Zamboanga del Norte"],
        ["Dapitan City", "Zamboanga del Norte"],
        ["Isabela City", "Basilan"],

        // BARMM
        ["Cotabato City", "Maguindanao del Norte"],
        ["Lamitan City", "Basilan"],

        // Central Visayas
        ["Cebu City", "Cebu"],
        ["Mandaue City", "Cebu"],
        ["Lapu-Lapu City", "Cebu"],
        ["Talisay City", "Cebu"],
        ["Carcar City", "Cebu"],
        ["Toledo City", "Cebu"],
        ["Danao City", "Cebu"],
        ["Bogo City", "Cebu"],
        ["Naga City", "Cebu"],
        ["Tagbilaran City", "Bohol"],
        ["Dumaguete City", "Negros Oriental"],

        // Western Visayas
        ["Bacolod City", "Negros Occidental"],
        ["Silay City", "Negros Occidental"],
        ["Iloilo City", "Iloilo"],
        ["Passi City", "Iloilo"],
        ["Roxas City", "Capiz"],
        ["Kabankalan City", "Negros Occidental"],
        ["Bago City", "Negros Occidental"],
        ["Cadiz City", "Negros Occidental"],
        ["Sagay City", "Negros Occidental"],
        ["Victorias City", "Negros Occidental"],

        // Eastern Visayas
        ["Tacloban City", "Leyte"],
        ["Ormoc City", "Leyte"],
        ["Calbayog City", "Samar"],
        ["Catbalogan City", "Samar"],
        ["Borongan City", "Eastern Samar"],
        ["Maasin City", "Southern Leyte"],
        ["Baybay City", "Leyte"],

        // Metro Manila
        ["Manila", "Metro Manila"],
        ["Quezon City", "Metro Manila"],
        ["Makati City", "Metro Manila"],
        ["Pasig City", "Metro Manila"],
        ["Taguig City", "Metro Manila"],
        ["Pasay City", "Metro Manila"],
        ["Caloocan City", "Metro Manila"],
        ["Mandaluyong City", "Metro Manila"],
        ["Marikina City", "Metro Manila"],
        ["Muntinlupa City", "Metro Manila"],
        ["Parañaque City", "Metro Manila"],
        ["Las Piñas City", "Metro Manila"],
        ["Valenzuela City", "Metro Manila"],
        ["San Juan City", "Metro Manila"],
        ["Malabon City", "Metro Manila"],
        ["Navotas City", "Metro Manila"],

        // Northern Luzon
        ["Baguio City", "Benguet"],
        ["Laoag City", "Ilocos Norte"],
        ["Vigan City", "Ilocos Sur"],
        ["Dagupan City", "Pangasinan"],
        ["Tuguegarao City", "Cagayan"],
        ["Santiago City", "Isabela"],
        ["Ilagan City", "Isabela"],
        ["Urdaneta City", "Pangasinan"],

        // Central Luzon
        ["Olongapo City", "Zambales"],
        ["Angeles City", "Pampanga"],
        ["San Fernando City", "Pampanga"],
        ["Tarlac City", "Tarlac"],
        ["Cabanatuan City", "Nueva Ecija"],
        ["Malolos City", "Bulacan"],
        ["San Jose del Monte City", "Bulacan"],
        ["Balanga City", "Bataan"],
        ["Mabalacat City", "Pampanga"],
        ["Gapan City", "Nueva Ecija"],
        ["Meycauayan City", "Bulacan"],

        // CALABARZON
        ["Antipolo City", "Rizal"],
        ["Calamba City", "Laguna"],
        ["Santa Rosa City", "Laguna"],
        ["San Pablo City", "Laguna"],
        ["Batangas City", "Batangas"],
        ["Lipa City", "Batangas"],
        ["Lucena City", "Quezon"],
        ["Bacoor City", "Cavite"],
        ["Imus City", "Cavite"],
        ["Dasmariñas City", "Cavite"],
        ["General Trias City", "Cavite"],
        ["Tagaytay City", "Cavite"],
        ["Biñan City", "Laguna"],
        ["Cabuyao City", "Laguna"],
        ["San Pedro City", "Laguna"],
        ["Tanauan City", "Batangas"],

        // Bicol Region
        ["Legazpi City", "Albay"],
        ["Naga City", "Camarines Sur"],
        ["Iriga City", "Camarines Sur"],
        ["Sorsogon City", "Sorsogon"],
        ["Tabaco City", "Albay"],
        ["Ligao City", "Albay"],
        ["Masbate City", "Masbate"],

        // MIMAROPA
        ["Puerto Princesa City", "Palawan"],
        ["Calapan City", "Oriental Mindoro"],
        ["Coron", "Palawan"],
        ["El Nido", "Palawan"],

    ].map(function (row) {
        return {
            name: row[0],
            province: row[1]
        };
    });


    // =========================================
    // POPULAR LOCATIONS
    // =========================================

    const POPULAR_CITIES = [
        "Iligan City",
        "Cagayan de Oro",
        "Davao City",
        "Cebu City",
        "Manila",
        "Pagadian City",
        "Zamboanga City"
    ];

    const MAX_RESULTS = 7;


    // =========================================
    // NORMALIZE SEARCH QUERY
    // =========================================

    function normalize(value) {
        return String(value || "")
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .trim()
            .toLowerCase()
            .replace(/\s+/g, " ");
    }


    // =========================================
    // MATCH AND RANK CITY SUGGESTIONS
    // =========================================

    function findSuggestions(query) {

        const search = normalize(query);

        const matches = LOCAL_CITIES.filter(function (city) {
            if (!search) {
                return POPULAR_CITIES.includes(city.name);
            }

            const name = normalize(city.name);
            const province = normalize(city.province);

            return (
                name.includes(search) ||
                province.includes(search)
            );
        });

        matches.sort(function (a, b) {

            if (!search) {
                return (
                    POPULAR_CITIES.indexOf(a.name) -
                    POPULAR_CITIES.indexOf(b.name)
                );
            }

            function score(city) {
                const name = normalize(city.name);
                const province = normalize(city.province);

                if (name.startsWith(search)) {
                    return 0;
                }

                if (name.includes(search)) {
                    return 1;
                }

                if (province.includes(search)) {
                    return 2;
                }

                return 3;
            }

            const difference = score(a) - score(b);

            if (difference !== 0) {
                return difference;
            }

            return a.name.localeCompare(b.name);
        });

        return matches.slice(0, MAX_RESULTS);
    }


    // =========================================
    // INITIALIZE AUTOCOMPLETE
    // =========================================

    function initializeAutocomplete(input, index) {

        /*
         * VERY IMPORTANT:
         *
         * Never attach a second autocomplete
         * to the Dashboard's custom city search.
         *
         * The Dashboard already includes:
         * - Saved Locations
         * - SAVED indicators
         * - Provincial descriptions
         * - Automatic search on selection
         */

        if (
            input.id === "dashboardCityInput" ||
            input.closest("#dashboardCityForm") ||
            input.dataset.phCityReady === "true"
        ) {
            return;
        }

        input.dataset.phCityReady = "true";

        input.setAttribute("autocomplete", "off");
        input.setAttribute("role", "combobox");
        input.setAttribute("aria-autocomplete", "list");
        input.setAttribute("aria-expanded", "false");

        const dropdown = document.createElement("div");

        const listId = "ph-city-dropdown-" + index;

        dropdown.id = listId;
        dropdown.className = "ph-city-dropdown";
        dropdown.setAttribute("role", "listbox");
        dropdown.hidden = true;

        input.setAttribute("aria-controls", listId);

        document.body.appendChild(dropdown);

        let visibleCities = [];
        let activeIndex = -1;


        // =====================================
        // POSITION DROPDOWN
        // =====================================

        function positionDropdown() {

            if (dropdown.hidden) {
                return;
            }

            const rect = input.getBoundingClientRect();

            const left = Math.max(8, rect.left);

            const width = Math.min(
                rect.width,
                window.innerWidth - left - 8
            );

            dropdown.style.left = left + "px";
            dropdown.style.width = width + "px";

            const roomBelow = window.innerHeight - rect.bottom;

            if (roomBelow < 230 && rect.top > roomBelow) {

                dropdown.style.top = "auto";

                dropdown.style.bottom = (
                    window.innerHeight - rect.top + 5
                ) + "px";

            } else {

                dropdown.style.bottom = "auto";

                dropdown.style.top = (
                    rect.bottom + 5
                ) + "px";
            }
        }


        // =====================================
        // CLOSE DROPDOWN
        // =====================================

        function closeDropdown() {

            dropdown.hidden = true;
            dropdown.replaceChildren();

            visibleCities = [];
            activeIndex = -1;

            input.setAttribute(
                "aria-expanded",
                "false"
            );

            input.removeAttribute(
                "aria-activedescendant"
            );
        }


        // =====================================
        // SELECT CITY
        // =====================================

        function selectCity(city) {

            input.value = city.name;

            closeDropdown();

            // Submit the existing search form.
            // Django then calls Nominatim.
            if (input.form) {

                if (input.form.requestSubmit) {
                    input.form.requestSubmit();
                } else {
                    input.form.submit();
                }
            }
        }


        // =====================================
        // HIGHLIGHT KEYBOARD SELECTION
        // =====================================

        function highlightSelection() {

            const options = dropdown.querySelectorAll(
                ".ph-city-option"
            );

            options.forEach(function (option, optionIndex) {

                const active = (
                    optionIndex === activeIndex
                );

                option.classList.toggle(
                    "active",
                    active
                );

                option.setAttribute(
                    "aria-selected",
                    active ? "true" : "false"
                );

                if (active) {

                    input.setAttribute(
                        "aria-activedescendant",
                        option.id
                    );

                    option.scrollIntoView({
                        block: "nearest"
                    });
                }
            });

            if (activeIndex < 0) {
                input.removeAttribute(
                    "aria-activedescendant"
                );
            }
        }


        // =====================================
        // SHOW CITY SUGGESTIONS
        // =====================================

        function showSuggestions() {

            visibleCities = findSuggestions(
                input.value
            );

            activeIndex = -1;

            dropdown.replaceChildren();

            if (!visibleCities.length) {
                closeDropdown();
                return;
            }

            const heading = document.createElement("div");

            heading.className = "ph-city-dropdown-heading";

            heading.textContent = input.value.trim()
                ? "Suggested Philippine Locations"
                : "Popular Philippine Locations";

            dropdown.appendChild(heading);


            visibleCities.forEach(function (city, itemIndex) {

                const option = document.createElement(
                    "button"
                );

                option.type = "button";
                option.className = "ph-city-option";

                option.id = (
                    listId + "-option-" + itemIndex
                );

                option.setAttribute(
                    "role",
                    "option"
                );

                option.setAttribute(
                    "aria-selected",
                    "false"
                );


                // Location icon
                const icon = document.createElement("span");

                icon.className = "ph-city-option-icon";

                const iconElement = document.createElement("i");

                iconElement.className = "bi bi-geo-alt";

                icon.appendChild(iconElement);


                // City and province
                const details = document.createElement("span");

                details.className = "ph-city-option-details";

                const name = document.createElement("span");

                name.className = "ph-city-option-name";
                name.textContent = city.name;

                const province = document.createElement("span");

                province.className = "ph-city-option-province";

                province.textContent = (
                    city.province + ", Philippines"
                );

                details.appendChild(name);
                details.appendChild(province);

                option.appendChild(icon);
                option.appendChild(details);


                // Mouse and touch selection
                option.addEventListener(
                    "pointerdown",
                    function (event) {
                        event.preventDefault();
                        selectCity(city);
                    }
                );

                // Keyboard or accessibility click
                option.addEventListener(
                    "click",
                    function () {
                        selectCity(city);
                    }
                );

                dropdown.appendChild(option);
            });


            const note = document.createElement("div");

            note.className = "ph-city-dropdown-note";

            note.textContent = (
                "Select a city to search automatically. " +
                "You can also type other Philippine locations."
            );

            dropdown.appendChild(note);

            dropdown.hidden = false;

            input.setAttribute(
                "aria-expanded",
                "true"
            );

            positionDropdown();
        }


        // =====================================
        // INPUT EVENTS
        // =====================================

        input.addEventListener(
            "input",
            showSuggestions
        );

        input.addEventListener(
            "focus",
            showSuggestions
        );


        // =====================================
        // KEYBOARD NAVIGATION
        // =====================================

        input.addEventListener(
            "keydown",
            function (event) {

                if (
                    event.key === "ArrowDown" ||
                    event.key === "ArrowUp"
                ) {

                    if (dropdown.hidden) {
                        showSuggestions();
                    }

                    if (!visibleCities.length) {
                        return;
                    }

                    event.preventDefault();

                    if (event.key === "ArrowDown") {

                        activeIndex = (
                            activeIndex + 1
                        ) % visibleCities.length;

                    } else {

                        activeIndex = activeIndex <= 0
                            ? visibleCities.length - 1
                            : activeIndex - 1;
                    }

                    highlightSelection();
                }

                else if (event.key === "Enter") {

                    if (
                        !dropdown.hidden &&
                        activeIndex >= 0
                    ) {

                        event.preventDefault();

                        selectCity(
                            visibleCities[activeIndex]
                        );
                    }

                    // Otherwise, normal Enter
                    // submits the typed city.
                }

                else if (
                    event.key === "Escape" ||
                    event.key === "Tab"
                ) {

                    closeDropdown();
                }
            }
        );


        // =====================================
        // CLICK OUTSIDE
        // =====================================

        document.addEventListener(
            "pointerdown",
            function (event) {

                if (
                    event.target !== input &&
                    !dropdown.contains(event.target)
                ) {

                    closeDropdown();
                }
            }
        );


        // =====================================
        // REPOSITION ON RESIZE OR SCROLL
        // =====================================

        window.addEventListener(
            "resize",
            positionDropdown
        );

        window.addEventListener(
            "scroll",
            positionDropdown,
            true
        );


        // =====================================
        // FORM SUBMISSION
        // =====================================

        if (input.form) {

            input.form.addEventListener(
                "submit",
                closeDropdown
            );
        }
    }


    // =========================================
    // FIND REGULAR CITY SEARCH INPUTS
    // =========================================

    function initializeCitySearches() {

        const inputs = document.querySelectorAll(
            'input[name="city"]'
        );

        inputs.forEach(function (input, index) {

            if (
                input.type !== "text" &&
                input.type !== "search"
            ) {
                return;
            }

            // Preserve the Dashboard's
            // existing Saved Locations autocomplete.
            if (
                input.id === "dashboardCityInput" ||
                input.closest("#dashboardCityForm")
            ) {
                return;
            }

            initializeAutocomplete(input, index);
        });
    }


    // =========================================
    // INITIALIZE AFTER PAGE LOAD
    // =========================================

    if (document.readyState === "loading") {

        document.addEventListener(
            "DOMContentLoaded",
            initializeCitySearches
        );

    } else {

        initializeCitySearches();
    }

})();
