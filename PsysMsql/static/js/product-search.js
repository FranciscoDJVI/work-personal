/**
 * Product Search Component
 * Funcionalidad de búsqueda de productos con navegación por teclado
 * Compatible con navegadores más antiguos
 */

function ProductSearch(options) {
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
  initializeEvents() {
    // Evento de input para búsqueda
    this.searchInput.addEventListener('input', (e) => this.handleInput(e));
    
    // Eventos de navegación con teclado
    this.searchInput.addEventListener('keydown', (e) => this.handleKeydown(e));
    
    // Ocultar resultados al hacer clic fuera
    document.addEventListener('click', (e) => this.handleClickOutside(e));
    
    console.log('ProductSearch inicializado correctamente');
  }

  /**
   * Manejar input de búsqueda
   */
  handleInput(event) {
    const query = event.target.value.trim();
    
    // Limpiar timeout anterior
    clearTimeout(this.searchTimeout);
    
    if (query.length >= this.config.minSearchLength) {
      // Esperar antes de buscar (debounce)
      this.searchTimeout = setTimeout(() => {
        this.searchProducts(query);
      }, this.config.debounceTime);
    } else {
      this.hideResults();
      this.resetSelection();
    }
  }

  /**
   * Manejar navegación con teclado
   */
  handleKeydown(event) {
    const resultItems = this.resultsContainer.querySelectorAll('.result-item');
    
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
  }

  /**
   * Manejar clics fuera del componente
   */
  handleClickOutside(event) {
    if (!this.searchInput.contains(event.target) && !this.resultsContainer.contains(event.target)) {
      this.hideResults();
      this.resetSelection();
    }
  }

  /**
   * Realizar búsqueda AJAX
   */
  async searchProducts(query) {
    const url = `${this.config.searchUrl}?q=${encodeURIComponent(query)}`;
    
    try {
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'Content-Type': 'application/json'
        },
        credentials: 'same-origin'
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(`HTTP ${response.status}: ${errorData.error || 'Error desconocido'}`);
      }

      const data = await response.json();
      
      if (data.results) {
        this.displayResults(data.results);
      } else {
        console.error('No se encontró el campo results en la respuesta:', data);
        this.hideResults();
      }
    } catch (error) {
      console.error('Error en búsqueda de productos:', error);
      this.showError(error.message);
    }
  }

  /**
   * Mostrar resultados de búsqueda
   */
  displayResults(results) {
    this.resultsContainer.innerHTML = '';
    this.availableProducts = results;
    this.resetSelection();
    
    if (results.length === 0) {
      this.showNoResults();
      return;
    }

    results.forEach((product, index) => {
      const resultItem = this.createResultItem(product, index);
      this.resultsContainer.appendChild(resultItem);
    });
    
    this.showResults();
  }

  /**
   * Crear elemento de resultado
   */
  createResultItem(product, index) {
    const resultItem = document.createElement('div');
    resultItem.className = 'result-item p-2 hover:bg-gray-100 cursor-pointer border-b border-gray-200';
    resultItem.setAttribute('data-index', index);
    
    resultItem.innerHTML = `
      <div class="font-medium text-black">${this.escapeHtml(product.name)}</div>
      <div class="text-sm text-gray-600">Precio: $${parseFloat(product.price).toLocaleString('es-CO')}</div>
    `;
    
    // Event listeners
    resultItem.addEventListener('click', () => this.selectProduct(product));
    resultItem.addEventListener('mouseenter', () => {
      this.currentSelectedIndex = index;
      this.updateSelection(this.resultsContainer.querySelectorAll('.result-item'));
    });
    
    return resultItem;
  }

  /**
   * Mostrar mensaje de "sin resultados"
   */
  showNoResults() {
    const noResultsDiv = document.createElement('div');
    noResultsDiv.className = 'p-2 text-gray-500';
    noResultsDiv.textContent = 'No se encontraron productos';
    this.resultsContainer.appendChild(noResultsDiv);
    this.availableProducts = [];
    this.showResults();
  }

  /**
   * Mostrar mensaje de error
   */
  showError(message) {
    this.resultsContainer.innerHTML = '';
    const errorDiv = document.createElement('div');
    errorDiv.className = 'p-2 text-red-500';
    errorDiv.textContent = `Error: ${message}`;
    this.resultsContainer.appendChild(errorDiv);
    this.showResults();
    
    // Ocultar error después de 3 segundos
    setTimeout(() => {
      this.hideResults();
    }, 3000);
  }

  /**
   * Seleccionar un producto
   */
  selectProduct(product) {
    this.searchInput.value = product.name;
    this.selectedProductInput.value = product.id;
    this.hideResults();
    this.resetSelection();
    
    // Enfocar campo de cantidad
    this.focusQuantityInput();
    
    console.log('Producto seleccionado:', product.name, 'ID:', product.id);
  }

  /**
   * Enfocar el campo de cantidad
   */
  focusQuantityInput() {
    const quantityInput = document.querySelector(`input[name="${this.config.quantityInputName}"]`);
    if (quantityInput) {
      setTimeout(() => quantityInput.focus(), 100);
    }
  }

  /**
   * Actualizar selección visual
   */
  updateSelection(resultItems) {
    // Remover clases de selección
    resultItems.forEach(item => {
      item.classList.remove('bg-blue-100', 'bg-blue-200');
    });
    
    // Agregar clase al elemento seleccionado
    if (this.currentSelectedIndex >= 0 && this.currentSelectedIndex < resultItems.length) {
      const selectedItem = resultItems[this.currentSelectedIndex];
      selectedItem.classList.add('bg-blue-100');
      
      // Scroll si es necesario
      selectedItem.scrollIntoView({
        behavior: 'smooth',
        block: 'nearest'
      });
    }
  }

  /**
   * Resetear selección
   */
  resetSelection() {
    this.currentSelectedIndex = -1;
  }

  /**
   * Mostrar contenedor de resultados
   */
  showResults() {
    this.resultsContainer.classList.remove('hidden');
  }

  /**
   * Ocultar contenedor de resultados
   */
  hideResults() {
    this.resultsContainer.classList.add('hidden');
  }

  /**
   * Escapar HTML para prevenir XSS
   */
  escapeHtml(text) {
    const map = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, (m) => map[m]);
  }

  /**
   * Obtener producto seleccionado actualmente
   */
  getSelectedProduct() {
    return {
      id: this.selectedProductInput.value,
      name: this.searchInput.value
    };
  }

  /**
   * Limpiar búsqueda
   */
  clear() {
    this.searchInput.value = '';
    this.selectedProductInput.value = '';
    this.hideResults();
    this.resetSelection();
    this.availableProducts = [];
  }

  /**
   * Destruir el componente y limpiar event listeners
   */
  destroy() {
    if (this.searchTimeout) {
      clearTimeout(this.searchTimeout);
    }
    // Aquí podrías remover event listeners si fuera necesario
    console.log('ProductSearch destruido');
  }
}

// Exportar para uso global
window.ProductSearch = ProductSearch;
