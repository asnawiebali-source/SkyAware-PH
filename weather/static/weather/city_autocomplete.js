
/*
 * SkyAware PH - Philippine City Autocomplete
 *
 * Autocomplete uses a local list only.
 * No API requests are made while typing.
 *
 * Nominatim is still used by the Django backend
 * when the user submits the search form.
 */

(function () {
    "use strict";

    // ==========================================
    // LOCAL PHILIPPINE CITY AND TOWN LIST
    // ==========================================

    const PHILIPPINE_PLACES = [

        // Metro Manila
        "Caloocan City",
        "Las Piñas City",
        "Makati City",
        "Malabon City",
        "Mandaluyong City",
        "Manila",
        "Marikina City",
        "Muntinlupa City",
        "Navotas City",
        "Parañaque City",
        "Pasay City",
        "Pasig City",
        "Quezon City",
        "San Juan City, Metro Manila",
        "Taguig City",
        "Valenzuela City",

        // Cordillera
        "Baguio City",
        "Tabuk City",

        // Ilocos Region
        "Alaminos City",
        "Batac City",
        "Candon City",
        "Dagupan City",
        "Laoag City",
        "San Carlos City, Pangasinan",
        "San Fernando City, La Union",
        "Urdaneta City",
        "Vigan City",

        // Cagayan Valley
        "Cauayan City",
        "Ilagan City",
        "Santiago City, Isabela",
        "Tuguegarao City",

        // Central Luzon
        "Angeles City",
        "Balanga City",
        "Baliwag City",
        "Cabanatuan City",
        "Gapan City",
        "Mabalacat City",
        "Malolos City",
        "Meycauayan City",
        "Muñoz City, Nueva Ecija",
        "Olongapo City",
        "Palayan City",
        "San Fernando City, Pampanga",
        "San Jose City, Nueva Ecija",
        "San Jose del Monte City",
        "Tarlac City",

        // CALABARZON
        "Antipolo City",
        "Bacoor City",
        "Batangas City",
        "Biñan City",
        "Cabuyao City",
        "Calaca City",
        "Calamba City",
        "Carmona City",
        "Cavite City",
        "Dasmariñas City",
        "General Trias City",
        "Imus City",
        "Lipa City",
        "Lucena City",
        "San Pablo City",
        "San Pedro City, Laguna",
        "Santa Rosa City, Laguna",
        "Santo Tomas City, Batangas",
        "Tagaytay City",
        "Tanauan City",
        "Tayabas City",
        "Trece Martires City",

        // MIMAROPA
        "Calapan City",
        "Puerto Princesa City",

        // Bicol Region
        "Iriga City",
        "Legazpi City",
        "Ligao City",
        "Masbate City",
        "Naga City, Camarines Sur",
        "Sorsogon City",
        "Tabaco City",

        // Western Visayas
        "Bacolod City",
        "Bago City",
        "Cadiz City",
        "Escalante City",
        "Himamaylan City",
        "Iloilo City",
        "Kabankalan City",
        "La Carlota City",
        "Passi City",
        "Roxas City",
        "Sagay City",
        "San Carlos City, Negros Occidental",
        "Silay City",
        "Sipalay City",
        "Talisay City, Negros Occidental",
        "Victorias City",

        // Negros Island Region
        "Bais City",
        "Bayawan City",
        "Canlaon City",
        "Dumaguete City",
        "Guihulngan City",
        "Tanjay City",

        // Central Visayas
        "Bogo City",
        "Carcar City",
        "Cebu City",
        "Danao City",
        "Lapu-Lapu City",
        "Mandaue City",
        "Naga City, Cebu",
        "Tagbilaran City",
        "Talisay City, Cebu",
        "Toledo City",

        // Eastern Visayas
        "Baybay City",
        "Borongan City",
        "Calbayog City",
        "Catbalogan City",
        "Maasin City",
        "Ormoc City",
        "Tacloban City",

        // Zamboanga Peninsula and Basilan
        "Dapitan City",
        "Dipolog City",
        "Isabela City, Basilan",
        "Pagadian City",
        "Zamboanga City",

        // Northern Mindanao
        "Cagayan de Oro City",
        "El Salvador City",
        "Gingoog City",
        "Iligan City",
        "Malaybalay City",
        "Oroquieta City",
        "Ozamiz City",
        "Tangub City",
        "Valencia City, Bukidnon",

        // Davao Region
        "Davao City",
        "Digos City",
        "Mati City",
        "Panabo City",
        "Samal City, Davao del Norte",
        "Tagum City",

        // SOCCSKSARGEN
        "General Santos City",
        "Kidapawan City",
        "Koronadal City",
        "Tacurong City",

        // Caraga
        "Bayugan City",
        "Bislig City",
        "Butuan City",
        "Cabadbaran City",
        "Surigao City",
        "Tandag City",

        // BARMM
        "Cotabato City",
        "Lamitan City",
        "Marawi City",

        // Additional municipalities and towns
        "Alubijid, Misamis Oriental",
        "Balingasag, Misamis Oriental",
        "Balingoan, Misamis Oriental",
        "Baroy, Lanao del Norte",
        "Clarin, Misamis Occidental",
        "Coron, Palawan",
        "El Nido, Palawan",
        "General Luna, Surigao del Norte",
        "Initao, Misamis Oriental",
        "Jasaan, Misamis Oriental",
        "Jimenez, Misamis Occidental",
        "Kauswagan, Lanao del Norte",
        "Kapatagan, Lanao del Norte",
        "Kolambugan, Lanao del Norte",
        "Linamon, Lanao del Norte",
        "Lugait, Misamis Oriental",
        "Manticao, Misamis Oriental",
        "Maramag, Bukidnon",
        "Medina, Misamis Oriental",
        "Naawan, Misamis Oriental",
        "Opol, Misamis Oriental",
        "Panglao, Bohol",
        "Plaridel, Misamis Occidental",
        "Siargao, Surigao del Norte",
        "Tubod, Lanao del Norte",
        "Villanueva, Misamis Oriental",

    ];


    // ==========================================
    // SEARCH CONFIGURATION
    // ==========================================

    const MAX_SUGGESTIONS = 8;

    const POPULAR_PLACES = [
        "Iligan City",
        "Cagayan de Oro City",
        "Cebu City",
        "Davao City",
        "Manila",
        "Pagadian City",
        "Zamboanga City",
        "General Santos City"
    ];


    // ==========================================
    // NORMALIZE SEARCH TEXT
    // ==========================================

    function normalizeText(value) {
        return String(value || "")
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .toLowerCase()
            .trim()
            .replace(/\s+/g, " ");
    }


    // ==========================================
    // PREPARE LOCAL DATA
    // ==========================================

    const PLACES = [...new Set(PHILIPPINE_PLACES)]
        .map(function (name) {
            return {
                name: name,
                search: normalizeText(name)
            };
        });


    // ==========================================
    // MATCH CITY NAMES
    // ==========================================

    function getSuggestions(query) {

        const search = normalizeText(query);

        // Show popular cities when the input is empty
        if (!search) {
            return POPULAR_PLACES.slice(
                0,
                MAX_SUGGESTIONS
            );
        }

        const matches = PLACES.filter(function (place) {
            return place.search.includes(search);
        });

        // Prioritize names starting with the query
        matches.sort(function (a, b) {

            const aStarts = a.search.startsWith(search);
            const bStarts = b.search.startsWith(search);

            if (aStarts && !bStarts) {
                return -1;
            }

            if (!aStarts && bStarts) {
                return 1;
            }

            return a.name.localeCompare(b.name);

        });

        return matches
            .slice(0, MAX_SUGGESTIONS)
            .map(function (place) {
                return place.name;
            });
    }


    // ==========================================
    // ATTACH AUTOCOMPLETE TO CITY INPUT
    // ==========================================

    function initializeAutocomplete(input, index) {

        if (input.dataset.phAutocomplete === "ready") {
            return;
        }

        input.dataset.phAutocomplete = "ready";

        // Disable the browser's saved-value dropdown
        input.setAttribute("autocomplete", "off");
        input.setAttribute("aria-autocomplete", "list");
        input.setAttribute("role", "combobox");
        input.setAttribute("aria-expanded", "false");

        const listId = "ph-city-suggestions-" + index;

        input.setAttribute("aria-controls", listId);

        // Append dropdown to body, avoiding
        // conflicts with Bootstrap input groups
        const dropdown = document.createElement("div");

        dropdown.id = listId;
        dropdown.className = "ph-city-dropdown";
        dropdown.setAttribute("role", "listbox");
        dropdown.setAttribute(
            "aria-label",
            "Philippine city suggestions"
        );

        dropdown.hidden = true;

        document.body.appendChild(dropdown);

        let currentSuggestions = [];
        let selectedIndex = -1;


        // ======================================
        // POSITION THE DROPDOWN
        // ======================================

        function positionDropdown() {

            if (dropdown.hidden) {
                return;
            }

            const rect = input.getBoundingClientRect();

            dropdown.style.left = rect.left + "px";
            dropdown.style.width = rect.width + "px";

            const roomBelow = (
                window.innerHeight - rect.bottom
            );

            if (
                roomBelow < 230
                && rect.top > roomBelow
            ) {

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


        // ======================================
        // CLOSE SUGGESTIONS
        // ======================================

        function closeDropdown() {

            dropdown.hidden = true;
            dropdown.replaceChildren();

            selectedIndex = -1;
            currentSuggestions = [];

            input.setAttribute(
                "aria-expanded",
                "false"
            );

            input.removeAttribute(
                "aria-activedescendant"
            );
        }


        // ======================================
        // SELECT A SUGGESTION
        // ======================================

        function selectSuggestion(name) {

            input.value = name;

            closeDropdown();

            input.focus();

            // Trigger input listeners without
            // submitting the search form.
            input.dispatchEvent(
                new Event("change", {
                    bubbles: true
                })
            );
        }


        // ======================================
        // KEYBOARD HIGHLIGHT
        // ======================================

        function updateHighlight() {

            const options = dropdown.querySelectorAll(
                '[role="option"]'
            );

            options.forEach(function (option, optionIndex) {

                const isSelected = (
                    optionIndex === selectedIndex
                );

                option.classList.toggle(
                    "active",
                    isSelected
                );

                option.setAttribute(
                    "aria-selected",
                    isSelected ? "true" : "false"
                );

                if (isSelected) {

                    input.setAttribute(
                        "aria-activedescendant",
                        option.id
                    );

                    option.scrollIntoView({
                        block: "nearest"
                    });
                }
            });

            if (selectedIndex < 0) {
                input.removeAttribute(
                    "aria-activedescendant"
                );
            }
        }


        // ======================================
        // RENDER MATCHING SUGGESTIONS
        // ======================================

        function showSuggestions() {

            currentSuggestions = getSuggestions(
                input.value
            );

            selectedIndex = -1;

            dropdown.replaceChildren();

            if (
                currentSuggestions.length === 0
            ) {

                closeDropdown();
                return;
            }

            const heading = document.createElement("div");

            heading.className = "ph-city-dropdown-heading";
            heading.textContent = "Suggested Philippine Locations";

            dropdown.appendChild(heading);

            currentSuggestions.forEach(
                function (name, suggestionIndex) {

                    const option = document.createElement(
                        "button"
                    );

                    option.type = "button";
                    option.className = "ph-city-option";

                    option.id = (
                        listId + "-option-" + suggestionIndex
                    );

                    option.setAttribute(
                        "role",
                        "option"
                    );

                    option.setAttribute(
                        "aria-selected",
                        "false"
                    );

                    const icon = document.createElement("span");

                    icon.className = "ph-city-option-icon";
                    icon.textContent = "📍";
                    icon.setAttribute(
                        "aria-hidden",
                        "true"
                    );

                    const label = document.createElement("span");

                    label.className = "ph-city-option-name";
                    label.textContent = name;

                    option.appendChild(icon);
                    option.appendChild(label);

                    option.addEventListener(
                        "pointerdown",
                        function (event) {

                            event.preventDefault();

                            selectSuggestion(name);

                        }
                    );

                    option.addEventListener(
                        "click",
                        function () {

                            selectSuggestion(name);

                        }
                    );

                    dropdown.appendChild(option);
                }
            );

            const note = document.createElement("div");

            note.className = "ph-city-dropdown-note";

            note.textContent = (
                "Select a location, then press Search. " +
                "Other Philippine towns can also be typed."
            );

            dropdown.appendChild(note);

            dropdown.hidden = false;

            input.setAttribute(
                "aria-expanded",
                "true"
            );

            positionDropdown();
        }


        // ======================================
        // INPUT EVENTS
        // ======================================

        input.addEventListener(
            "input",
            showSuggestions
        );

        input.addEventListener(
            "focus",
            showSuggestions
        );


        // ======================================
        // KEYBOARD NAVIGATION
        // ======================================

        input.addEventListener(
            "keydown",
            function (event) {

                if (
                    event.key === "ArrowDown"
                    || event.key === "ArrowUp"
                ) {

                    if (dropdown.hidden) {
                        showSuggestions();
                    }

                    if (!currentSuggestions.length) {
                        return;
                    }

                    event.preventDefault();

                    if (event.key === "ArrowDown") {

                        selectedIndex = (
                            selectedIndex + 1
                        ) % currentSuggestions.length;

                    } else {

                        selectedIndex = (
                            selectedIndex <= 0
                                ? currentSuggestions.length - 1
                                : selectedIndex - 1
                        );

                    }

                    updateHighlight();
                }

                else if (event.key === "Enter") {

                    // If the user highlighted a city,
                    // select it instead of submitting.
                    if (
                        !dropdown.hidden
                        && selectedIndex >= 0
                    ) {

                        event.preventDefault();

                        selectSuggestion(
                            currentSuggestions[selectedIndex]
                        );
                    }

                    // Otherwise let the form submit.

                }

                else if (
                    event.key === "Escape"
                    || event.key === "Tab"
                ) {

                    closeDropdown();

                }

            }
        );


        // ======================================
        // CLICKING OUTSIDE
        // ======================================

        document.addEventListener(
            "pointerdown",
            function (event) {

                if (
                    event.target !== input
                    && !dropdown.contains(event.target)
                ) {

                    closeDropdown();

                }
            }
        );


        // ======================================
        // SCREEN RESIZE AND SCROLL
        // ======================================

        window.addEventListener(
            "resize",
            positionDropdown
        );

        window.addEventListener(
            "scroll",
            positionDropdown,
            true
        );


        // ======================================
        // FORM SUBMISSION
        // ======================================

        if (input.form) {

            input.form.addEventListener(
                "submit",
                closeDropdown
            );

        }
    }


    // ==========================================
    // INITIALIZE ALL CITY SEARCH INPUTS
    // ==========================================

    function initializeAllCityInputs() {

        const inputs = document.querySelectorAll(
            'input[name="city"]'
        );

        inputs.forEach(
            function (input, index) {

                if (
                    input.type === "text"
                    || input.type === "search"
                ) {

                    initializeAutocomplete(
                        input,
                        index
                    );

                }
            }
        );

    }


    if (document.readyState === "loading") {

        document.addEventListener(
            "DOMContentLoaded",
            initializeAllCityInputs
        );

    } else {

        initializeAllCityInputs();

    }

})();
