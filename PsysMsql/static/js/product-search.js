/**
 * Product Search Component
 * Funcionalidad de búsqueda de productos con navegación por teclado
 * Compatible con navegadores más antiguos (ES5)
 */

function ProductSearch(options) {
  var self = this;
  options = options || {};
  
  // Configuración por defecto
  this.config = {
    searchInputId: 'product-search-input',
    resultsContainerId: 'search-results',
    selectedProductInputId: 'selected-product-id',
    quantityInputName: 'totalsell',
    searchUrl: options.searchUrl || '/app/search-products-ajax/',
    minSearchLength: 2,
    debounceTime: 300,
    maxResults: 10
  };
  
  // Copiar opciones personalizadas
  for (var key in options) {
    if (options.hasOwnProperty(key)) {
      this.config[key] = options[key];
    }
  }

  // Variables de estado
  this.searchTimeout = null;
  this.currentSelectedIndex = -1;
  this.availableProducts = [];
  
  // Elementos DOM
  this.searchInput = document.getElementById(this.config.searchInputId);
  this.resultsContainer = document.getElementById(this.config.resultsContainerId);
  this.selectedProductInput = document.getElementById(this.config.selectedProductInputId);
  
  // Inicializar eventos si los elementos existen
  if (this.searchInput && this.resultsContainer && this.selectedProductInput) {
    this.initializeEvents();
  }
}

/**
 * Inicializar todos los event listeners
 */
ProductSearch.prototype.initializeEvents = function() {
  var self = this;
  
  // Evento de input para búsqueda
  this.searchInput.addEventListener('input', function(e) {
    self.handleInput(e);
  });
  
  // Eventos de navegación con teclado
  this.searchInput.addEventListener('keydown', function(e) {
    self.handleKeydown(e);
  });
  
  // Ocultar resultados al hacer clic fuera
  document.addEventListener('click', function(e) {
    self.handleClickOutside(e);
  });
  
  console.log('ProductSearch inicializado correctamente');
};

/**
 * Manejar input de búsqueda
 */
ProductSearch.prototype.handleInput = function(event) {
  var self = this;
  var query = event.target.value.trim();
  
  // Limpiar timeout anterior
  clearTimeout(this.searchTimeout);
  
  if (query.length >= this.config.minSearchLength) {
    // Esperar antes de buscar (debounce)
    this.searchTimeout = setTimeout(function() {
      self.searchProducts(query);
    }, this.config.debounceTime);
  } else {
    this.hideResults();
    this.resetSelection();
  }
};

/**
 * Manejar navegación con teclado
 */
ProductSearch.prototype.handleKeydown = function(event) {
  var resultItems = this.resultsContainer.querySelectorAll('.result-item');
  
  switch(event.key) {
    case 'ArrowDown':
      event.preventDefault();
      if (resultItems.length > 0) {
        this.currentSelectedIndex = Math.min(this.currentSelectedIndex + 1, resultItems.length - 1);
        this.updateSelection(resultItems);
      }
      break;
      
    case 'ArrowUp':
      event.preventDefault();
      if (resultItems.length > 0) {
        this.currentSelectedIndex = Math.max(this.currentSelectedIndex - 1, -1);
        this.updateSelection(resultItems);
      }
      break;
      
    case 'Enter':
      event.preventDefault();
      if (this.currentSelectedIndex >= 0 && this.currentSelectedIndex < this.availableProducts.length) {
        this.selectProduct(this.availableProducts[this.currentSelectedIndex]);
      } else if (this.availableProducts.length === 1) {
        // Seleccionar automáticamente si solo hay un resultado
        this.selectProduct(this.availableProducts[0]);
      }
      break;
      
    case 'Escape':
      event.preventDefault();
      this.hideResults();
      this.resetSelection();
      break;
  }
};

/**
 * Manejar clics fuera del componente
 */
ProductSearch.prototype.handleClickOutside = function(event) {
  if (!this.searchInput.contains(event.target) && !this.resultsContainer.contains(event.target)) {
    this.hideResults();
    this.resetSelection();
  }
};

/**
 * Realizar búsqueda AJAX
 */
ProductSearch.prototype.searchProducts = function(query) {
  var self = this;
  var url = this.config.searchUrl + '?q=' + encodeURIComponent(query);
  
  fetch(url, {
    method: 'GET',
    headers: {
      'X-Requested-With': 'XMLHttpRequest',
      'Content-Type': 'application/json'
    },
    credentials: 'same-origin'
  })
  .then(function(response) {
    console.log('Response status:', response.status);
    if (!response.ok) {
      return response.json().then(function(err) {
        throw new Error('HTTP ' + response.status + ': ' + (err.error || 'Error desconocido'));
      }).catch(function() {
        throw new Error('HTTP ' + response.status + ': Error desconocido');
      });
    }
    return response.json();
  })
  .then(function(data) {
    console.log('Search results:', data);
    if (data.results) {
      self.displayResults(data.results);
    } else {
      console.error('No se encontró el campo results en la respuesta:', data);
      self.hideResults();
    }
  })
  .catch(function(error) {
    console.error('Error en búsqueda de productos:', error);
    self.showError(error.message);
  });
};

/**
 * Mostrar resultados de búsqueda
 */
ProductSearch.prototype.displayResults = function(results) {
  var self = this;
  this.resultsContainer.innerHTML = '';
  this.availableProducts = results;
  this.resetSelection();
  
  if (results.length === 0) {
    this.showNoResults();
    return;
  }

  for (var i = 0; i < results.length; i++) {
    var resultItem = this.createResultItem(results[i], i);
    this.resultsContainer.appendChild(resultItem);
  }
  
  this.showResults();
};

/**
 * Crear elemento de resultado
 */
ProductSearch.prototype.createResultItem = function(product, index) {
  var self = this;
  var resultItem = document.createElement('div');
  resultItem.className = 'result-item p-2 hover:bg-gray-100 cursor-pointer border-b border-gray-200';
  resultItem.setAttribute('data-index', index);
  
  resultItem.innerHTML = 
    '<div class="font-medium text-black">' + this.escapeHtml(product.name) + '</div>' +
    '<div class="text-sm text-gray-600">Precio: $' + parseFloat(product.price).toLocaleString('es-CO') + '</div>';
  
  // Event listeners
  resultItem.addEventListener('click', function() {
    self.selectProduct(product);
  });
  
  resultItem.addEventListener('mouseenter', function() {
    self.currentSelectedIndex = index;
    self.updateSelection(self.resultsContainer.querySelectorAll('.result-item'));
  });
  
  return resultItem;
};

/**
 * Mostrar mensaje de "sin resultados"
 */
ProductSearch.prototype.showNoResults = function() {
  var noResultsDiv = document.createElement('div');
  noResultsDiv.className = 'p-2 text-gray-500';
  noResultsDiv.textContent = 'No se encontraron productos';
  this.resultsContainer.appendChild(noResultsDiv);
  this.availableProducts = [];
  this.showResults();
};

/**
 * Mostrar mensaje de error
 */
ProductSearch.prototype.showError = function(message) {
  var self = this;
  this.resultsContainer.innerHTML = '';
  var errorDiv = document.createElement('div');
  errorDiv.className = 'p-2 text-red-500';
  errorDiv.textContent = 'Error: ' + message;
  this.resultsContainer.appendChild(errorDiv);
  this.showResults();
  
  // Ocultar error después de 3 segundos
  setTimeout(function() {
    self.hideResults();
  }, 3000);
};

/**
 * Seleccionar un producto
 */
ProductSearch.prototype.selectProduct = function(product) {
  this.searchInput.value = product.name;
  this.selectedProductInput.value = product.id;
  this.hideResults();
  this.resetSelection();
  
  // Enfocar campo de cantidad
  this.focusQuantityInput();
  
  console.log('Producto seleccionado:', product.name, 'ID:', product.id);
};

/**
 * Enfocar el campo de cantidad
 */
ProductSearch.prototype.focusQuantityInput = function() {
  var quantityInput = document.querySelector('input[name="' + this.config.quantityInputName + '"]');
  if (quantityInput) {
    setTimeout(function() {
      quantityInput.focus();
    }, 100);
  }
};

/**
 * Actualizar selección visual
 */
ProductSearch.prototype.updateSelection = function(resultItems) {
  // Remover clases de selección
  for (var i = 0; i < resultItems.length; i++) {
    resultItems[i].classList.remove('bg-blue-100', 'bg-blue-200');
  }
  
  // Agregar clase al elemento seleccionado
  if (this.currentSelectedIndex >= 0 && this.currentSelectedIndex < resultItems.length) {
    var selectedItem = resultItems[this.currentSelectedIndex];
    selectedItem.classList.add('bg-blue-100');
    
    // Scroll si es necesario
    selectedItem.scrollIntoView({
      behavior: 'smooth',
      block: 'nearest'
    });
  }
};

/**
 * Resetear selección
 */
ProductSearch.prototype.resetSelection = function() {
  this.currentSelectedIndex = -1;
};

/**
 * Mostrar contenedor de resultados
 */
ProductSearch.prototype.showResults = function() {
  this.resultsContainer.classList.remove('hidden');
};

/**
 * Ocultar contenedor de resultados
 */
ProductSearch.prototype.hideResults = function() {
  this.resultsContainer.classList.add('hidden');
};

/**
 * Escapar HTML para prevenir XSS
 */
ProductSearch.prototype.escapeHtml = function(text) {
  var map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };
  return text.replace(/[&<>"']/g, function(m) {
    return map[m];
  });
};

/**
 * Obtener producto seleccionado actualmente
 */
ProductSearch.prototype.getSelectedProduct = function() {
  return {
    id: this.selectedProductInput.value,
    name: this.searchInput.value
  };
};

/**
 * Limpiar búsqueda
 */
ProductSearch.prototype.clear = function() {
  this.searchInput.value = '';
  this.selectedProductInput.value = '';
  this.hideResults();
  this.resetSelection();
  this.availableProducts = [];
};

/**
 * Destruir el componente y limpiar event listeners
 */
ProductSearch.prototype.destroy = function() {
  if (this.searchTimeout) {
    clearTimeout(this.searchTimeout);
  }
  console.log('ProductSearch destruido');
};

// Exportar para uso global
window.ProductSearch = ProductSearch;
