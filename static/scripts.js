/*
 * Copyright 2024 The Apache Software Foundation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
const searchInput = document.getElementById('searchInput');
const queryInput = document.getElementById('queryInput');
const queryButton = document.getElementById('queryButton');
const clearButton = document.getElementById('clearButton');
const projectModal = document.getElementById('projectModal');
const closeModal = document.getElementById('closeModal');
const modalTitle = document.getElementById('modalTitle');
const projectDetails = document.getElementById('projectDetails');
const loading = document.getElementById('loading');
const suggestedStack = document.getElementById('suggestedStack');
const defaultView = document.getElementById('defaultView');
const filteredView = document.getElementById('filteredView');
const categoryFilters = document.getElementById('categoryFilters');
const visualization = document.getElementById('visualization');

let allProjects = [];

queryButton.addEventListener('click', queryProjects);
clearButton.addEventListener('click', clearQuery);
closeModal.addEventListener('click', () => projectModal.classList.add('hidden'));
queryInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        queryProjects();
    }
});
searchInput.addEventListener('input', filterProjectsByName);

const dimensionSelector = document.getElementById('dimensionSelector');
dimensionSelector.addEventListener('change', loadProjects);

loadProjects();

function showLoading() {
    loading.classList.remove('hidden');
}

function hideLoading() {
    loading.classList.add('hidden');
}

const toggleAllCategoriesButton = document.getElementById('toggleAllCategories');
let allCategoriesSelected = true;

toggleAllCategoriesButton.addEventListener('click', toggleAllCategories);

function loadProjects() {
    showLoading();
    const dimension = dimensionSelector.value;
    fetch(`/api/projects?dimension=${dimension}`)
        .then(response => response.json())
        .then(data => {
            allProjects = data.categories;
            renderCategoryFilters(data.categories, data.current_dimension);
            renderProjects(data.categories);
            hideLoading();
        })
        .catch(error => {
            console.error('Error loading projects:', error);
            hideLoading();
        });
}

function renderCategoryFilters(categories, dimension) {
    categoryFilters.innerHTML = '';
    toggleAllCategoriesButton.textContent = `Deselect All ${dimension}s`;
    categories.forEach(category => {
        const filterDiv = document.createElement('div');
        filterDiv.className = 'flex items-center';
        const isChecked = true;
        filterDiv.innerHTML = `
            <input type="checkbox" id="${category.name}" name="${category.name}" ${isChecked ? 'checked' : ''} class="mr-2 category-checkbox">
            <label for="${category.name}" class="text-sm">${category.name} (${category.projects.length})</label>
        `;
        const checkbox = filterDiv.querySelector('input');
        checkbox.addEventListener('change', () => toggleCategory(category.name, checkbox.checked));
        categoryFilters.appendChild(filterDiv);
    });
    updateToggleAllButton();
}

function toggleAllCategories() {
    allCategoriesSelected = !allCategoriesSelected;
    const checkboxes = document.querySelectorAll('.category-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.checked = allCategoriesSelected;
        toggleCategory(checkbox.name, allCategoriesSelected, false);
    });
    updateToggleAllButton();
}

function updateToggleAllButton() {
    const checkboxes = document.querySelectorAll('.category-checkbox');
    allCategoriesSelected = Array.from(checkboxes).every(checkbox => checkbox.checked);
    toggleAllCategoriesButton.textContent = allCategoriesSelected ? 'Deselect All' : 'Select All';
}

function toggleCategory(categoryName, isChecked, shouldUpdateToggleAllButton = true) {
    const categorySection = document.querySelector(`.category-section[data-category="${categoryName}"]`);
    if (categorySection) {
        categorySection.style.display = isChecked ? 'block' : 'none';
    }
    if (shouldUpdateToggleAllButton) {
        updateToggleAllButton();
    }
}

function renderProjects(categories) {
    visualization.innerHTML = '';
    categories.forEach(category => {
        const categorySection = document.createElement('div');
        categorySection.className = 'category-section mb-8';
        categorySection.dataset.category = category.name;
        categorySection.innerHTML = `
            <h2 class="text-2xl font-bold mb-4">${category.name}</h2>
            <div class="project-grid grid grid-cols-4 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-8 gap-4"></div>
        `;
        const projectGrid = categorySection.querySelector('.project-grid');
        category.projects.forEach(project => {
            const projectCard = createProjectCard(project, category.name);
            projectGrid.appendChild(projectCard);
        });
        visualization.appendChild(categorySection);
    });
    toggleCategory('Retired', false);
}

function createProjectCard(project, categoryName, isFilteredView = false) {
    const card = document.createElement('div');
    const logoPlaceholder = generateLogoPlaceholder(project.name, isFilteredView ? 60 : 32);
    
    if (isFilteredView) {
        card.className = 'filtered-project-card';
        card.innerHTML = `
            <div class="w-16 h-16 mr-3 flex-shrink-0">
                ${project.logo ? `<img src="${project.logo}" alt="${project.name} logo" class="w-full h-full object-contain">` : logoPlaceholder}
            </div>
            <div class="flex-grow">
                <h3 class="text-base font-semibold mb-1">${project.name}</h3>
                <p class="text-xs text-gray-600 mb-1">${project.shortdesc}</p>
                ${project.role ? `<p class="text-xs text-gray-500"><strong>Role:</strong> ${project.role}</p>` : ''}
                <p class="text-xs text-gray-500"><strong>Reason:</strong> ${project.filter_explanation}</p>
                <p class="text-xs text-gray-500 mt-2"><strong>Similar Projects:</strong> ${project.similar_projects.join(', ') || 'None'}</p>
            </div>
        `;
    } else {
        card.className = 'project-card';
        card.dataset.category = categoryName;
        card.innerHTML = `
            <div class="w-8 h-8 mb-1">
                ${project.logo ? `<img src="${project.logo}" alt="${project.name} logo" class="w-full h-full object-contain">` : logoPlaceholder}
            </div>
            <div class="project-name">${project.name}</div>
        `;
    }
    
    card.addEventListener('click', () => showProjectDetails(project));
    return card;
}

function generateLogoPlaceholder(projectName, size) {
    const initials = projectName
        .split(' ')
        .map(word => word[0])
        .join('')
        .substring(0, 2)
        .toUpperCase();

    const colors = [
        '#FFA07A', '#98FB98', '#87CEFA', '#DDA0DD', '#F0E68C',
        '#E6E6FA', '#FFA500', '#20B2AA', '#FF6347', '#00FA9A'
    ];
    const colorIndex = projectName.length % colors.length;
    const bgColor = colors[colorIndex];

    return `
        <svg width="${size}" height="${size}" xmlns="http://www.w3.org/2000/svg">
            <rect width="${size}" height="${size}" fill="${bgColor}" />
            <text x="${size/2}" y="${size/2}" font-family="Arial, sans-serif" font-size="${size/2}" fill="#000000" text-anchor="middle" dominant-baseline="central">${initials}</text>
        </svg>
    `;
}

function queryProjects() {
    const query = queryInput.value;
    if (query) {
        showLoading();
        fetch(`/api/filter?query=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                renderSuggestedStacks(data.stacks, data.projects);
                defaultView.classList.add('hidden');
                filteredView.classList.remove('hidden');
                categoryFilters.classList.add('hidden');
                document.getElementById('toggleAllCategories').classList.add('hidden');
                document.getElementById('searchInput').classList.add('hidden');
                document.getElementById('dimensionSelector').classList.add('hidden');
                hideLoading();
            })
            .catch(error => {
                console.error('Error querying projects:', error);
                hideLoading();
            });
    }
}


function renderSuggestedStacks(stacks, projects) {
    const suggestedStacksContainer = document.getElementById('suggestedStacks');
    suggestedStacksContainer.innerHTML = '';

    if (stacks.length === 0) {
        suggestedStacksContainer.innerHTML = '<p>No suggested stacks found.</p>';
        return;
    }

    stacks.forEach(stack => {
        const stackCard = document.createElement('div');
        stackCard.className = 'stack-card';
        stackCard.innerHTML = `
            <h3 class="stack-title">${stack.name}</h3>
            <p class="stack-description">${stack.description}</p>
            <div class="stack-projects">
                ${stack.projects.map(projectName => `<span class="stack-project">${projectName}</span>`).join('')}
            </div>
        `;
        suggestedStacksContainer.appendChild(stackCard);
    });

    // Render filtered projects
    const filteredProjectsCard = document.createElement('div');
    filteredProjectsCard.className = 'stack-card';
    filteredProjectsCard.innerHTML = '<h3 class="stack-title">Relevant Projects</h3>';
    const projectList = document.createElement('div');
    projectList.className = 'space-y-4';
    projects.forEach(project => {
        const projectCard = createProjectCard(project, project.category, true);
        projectList.appendChild(projectCard);
    });
    filteredProjectsCard.appendChild(projectList);
    suggestedStacksContainer.appendChild(filteredProjectsCard);
}

function clearQuery() {
    queryInput.value = '';
    defaultView.classList.remove('hidden');
    filteredView.classList.add('hidden');
    categoryFilters.classList.remove('hidden');
    document.getElementById('toggleAllCategories').classList.remove('hidden');
    document.getElementById('searchInput').classList.remove('hidden');
    document.getElementById('dimensionSelector').classList.remove('hidden');
    suggestedStacks.innerHTML = '';
}

function renderSuggestedStack(projects) {
    suggestedStack.innerHTML = '';
    projects.forEach(project => {
        const projectCard = createProjectCard(project, project.category, true);
        suggestedStack.appendChild(projectCard);
    });
}

function showProjectDetails(project) {
    modalTitle.textContent = project.name;
    projectDetails.innerHTML = `
        <div class="flex items-center mb-4">
            <div class="w-20 h-20 mr-4">
                ${project.logo ? `<img src="${project.logo}" alt="${project.name} logo" class="w-full h-full object-contain">` : generateLogoPlaceholder(project.name, 80)}
            </div>
            <div>
                <p><strong>Category:</strong> ${project.category}</p>
                <p><strong>Programming Language:</strong> ${project.programming_language}</p>
            </div>
        </div>
        <p><strong>Description:</strong> ${project.description || project.shortdesc}</p>
        ${project.role ? `<p><strong>Role in Stack:</strong> ${project.role}</p>` : ''}
        ${project.filter_explanation ? `<p><strong>Reason for Selection:</strong> ${project.filter_explanation}</p>` : ''}
        <div class="mt-2">
            <strong>Features:</strong>
            ${project.features ? project.features.map(feature => `<span class="feature-tag">${feature}</span>`).join('') : 'No features listed'}
        </div>
        <p class="mt-2"><strong>Similar Projects:</strong></p>
        <div class="similar-projects-list">
            ${project.similar_projects.map(sp => `<a href="#" class="similar-project-link" data-project="${sp}">${sp}</a>`).join(', ')}
        </div>
        ${project.homepage ? `<p><strong>Homepage:</strong> <a href="${project.homepage}" target="_blank" class="text-blue-500">${project.homepage}</a></p>` : ''}
        ${project.download_page ? `<p><strong>Download Page:</strong> <a href="${project.download_page}" target="_blank" class="text-blue-500">${project.download_page}</a></p>` : ''}
        ${project.latest_release ? `
        <div class="mt-4">
            <h3 class="text-lg font-semibold">Latest Release</h3>
            <p><strong>Version:</strong> ${project.latest_release.version}</p>
            <p><strong>Date:</strong> ${project.latest_release.date}</p>
            ${project.latest_release.download_url ? `<p><strong>Download:</strong> <a href="${project.latest_release.download_url}" target="_blank" class="text-blue-500">Download</a></p>` : ''}
        </div>
        ` : ''}
    `;

    // Add click event listeners to similar project links
    const similarProjectLinks = projectDetails.querySelectorAll('.similar-project-link');
    similarProjectLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const similarProjectName = e.target.dataset.project;
            let foundProject = null;
            allProjects.forEach(category => {
                category.projects.forEach(project => {
                    if (project.name === similarProjectName) {
                        foundProject = project;
                        return; // Exit the inner loop once found
                    }
                });
                if (foundProject) return; // Exit the outer loop once found
            });
            if (foundProject) {
                showProjectDetails(foundProject);
            } else {
                console.log(`Project ${similarProjectName} not found.`);
            }
        });
    });

    projectModal.classList.remove('hidden');
}

function compareProjects(project1, project2) {
    fetch(`/api/compare?project1=${encodeURIComponent(project1)}&project2=${encodeURIComponent(project2)}`)
        .then(response => response.json())
        .then(data => {
            const comparisonDetails = document.getElementById('comparisonDetails');
            comparisonDetails.innerHTML = `
                <div>
                    <h3 class="text-xl font-bold">${data.project1.name}</h3>
                    <p>${data.project1.shortdesc}</p>
                    <p><strong>Category:</strong> ${data.project1.category}</p>
                    <div class="mt-2">
                        <strong>Features:</strong>
                        ${data.project1.features.map(feature => `<span class="feature-tag">${feature}</span>`).join('')}
                    </div>
                </div>
                <div>
                    <h3 class="text-xl font-bold">${data.project2.name}</h3>
                    <p>${data.project2.shortdesc}</p>
                    <p><strong>Category:</strong> ${data.project2.category}</p>
                    <div class="mt-2">
                        <strong>Features:</strong>
                        ${data.project2.features.map(feature => `<span class="feature-tag">${feature}</span>`).join('')}
                    </div>
                </div>
                <div class="col-span-2 text-center mt-4">
                    <p><strong>Similarity Score:</strong> ${(data.similarity_score * 100).toFixed(2)}%</p>
                </div>
            `;
            document.getElementById('comparisonModal').classList.remove('hidden');
        })
        .catch(error => console.error('Error comparing projects:', error));
}

// Add new JavaScript for project comparison
document.getElementById('openCompareModal').addEventListener('click', function() {
    document.getElementById('comparisonModal').classList.remove('hidden');
});

document.getElementById('closeComparisonModal').addEventListener('click', function() {
    document.getElementById('comparisonModal').classList.add('hidden');
});

document.getElementById('compareFromDetails').addEventListener('click', function() {
    const projectName = document.getElementById('modalTitle').textContent;
    document.getElementById('compareProject1').value = projectName;
    document.getElementById('projectModal').classList.add('hidden');
    document.getElementById('comparisonModal').classList.remove('hidden');
});

function filterProjectsByName() {
    const searchTerm = searchInput.value.toLowerCase();
    const projectCards = document.querySelectorAll('.project-card');
    
    projectCards.forEach(card => {
        const projectName = card.querySelector('.project-name').textContent.toLowerCase();
        if (projectName.includes(searchTerm)) {
            card.style.display = 'flex';
        } else {
            card.style.display = 'none';
        }
    });

    const categorySections = document.querySelectorAll('.category-section');
    categorySections.forEach(section => {
        const visibleProjects = section.querySelectorAll('.project-card[style="display: flex;"]');
        section.style.display = visibleProjects.length > 0 ? 'block' : 'none';
    });
}

// Add autocomplete functionality
function setupAutocomplete(inputId) {
    const input = document.getElementById(inputId);
    let timeout = null;

    input.addEventListener('input', function() {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            const query = this.value;
            if (query.length > 1) {
                fetch(`/api/project_names?query=${encodeURIComponent(query)}`)
                    .then(response => response.json())
                    .then(projectNames => {
                        // Create and show autocomplete suggestions
                        const datalist = document.createElement('datalist');
                        datalist.id = `${inputId}-list`;
                        projectNames.forEach(name => {
                            const option = document.createElement('option');
                            option.value = name;
                            datalist.appendChild(option);
                        });
                        document.body.appendChild(datalist);
                        input.setAttribute('list', `${inputId}-list`);
                    });
            }
        }, 300);
    });
}

setupAutocomplete('compareProject1');
setupAutocomplete('compareProject2');
setupAutocomplete('compareProject3');
setupAutocomplete('compareProject4');

// Comparison functionality
document.getElementById('compareBtn').addEventListener('click', function() {
    const projects = [
        document.getElementById('compareProject1').value,
        document.getElementById('compareProject2').value,
        document.getElementById('compareProject3').value,
        document.getElementById('compareProject4').value
    ].filter(Boolean);

    if (projects.length < 2) {
        alert('Please select at least two projects to compare.');
        return;
    }

    fetch(`/api/compare?${projects.map(p => `projects=${encodeURIComponent(p)}`).join('&')}`)
        .then(response => response.json())
        .then(data => {
            const comparisonDetails = document.getElementById('comparisonDetails');
            comparisonDetails.innerHTML = '';

            data.projects.forEach(project => {
                const projectDiv = document.createElement('div');
                projectDiv.className = 'bg-gray-100 p-4 rounded';
                projectDiv.innerHTML = `
                    <h3 class="text-xl font-bold mb-2">${project.name}</h3>
                    <p class="mb-2"><strong>Category:</strong> ${project.category}</p>
                    <p class="mb-2"><strong>Description:</strong> ${project.shortdesc}</p>
                    <p><strong>Features:</strong></p>
                    <ul class="list-disc pl-5">
                        ${project.features.map(feature => `<li>${feature}</li>`).join('')}
                    </ul>
                `;
                comparisonDetails.appendChild(projectDiv);
            });

            document.getElementById('comparisonModal').classList.remove('hidden');
        });
});

