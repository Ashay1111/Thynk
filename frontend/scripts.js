const API_BASE = ''
const selectedDocuments = new Set()
let currentIndexParameters = { chunk_size: 800, chunk_overlap: 150 }
let documentsNeedReindexing = false

// Initialize the application
document.addEventListener('DOMContentLoaded', function () {
  loadDocuments()
  setupEventListeners()
  setupParameterChangeListeners()
})

function setupEventListeners () {
  // File input change
  document
    .getElementById('fileInput')
    .addEventListener('change', handleFileSelect)

  // Drag and drop
  const uploadArea = document.getElementById('uploadArea')
  uploadArea.addEventListener('click', () =>
    document.getElementById('fileInput').click()
  )
  uploadArea.addEventListener('dragover', handleDragOver)
  uploadArea.addEventListener('dragleave', handleDragLeave)
  uploadArea.addEventListener('drop', handleDrop)

  // Enter key for query submission
  document
    .getElementById('queryInput')
    .addEventListener('keypress', function (e) {
      if (e.key === 'Enter' && e.ctrlKey) {
        submitQuery()
      }
    })
}

function setupParameterChangeListeners () {
  // Monitor chunk parameters for changes
  const chunkSizeInput = document.getElementById('chunkSize')
  const chunkOverlapInput = document.getElementById('chunkOverlap')

  function checkParameterChange () {
    const currentChunkSize = parseInt(chunkSizeInput.value)
    const currentChunkOverlap = parseInt(chunkOverlapInput.value)

    if (
      currentChunkSize !== currentIndexParameters.chunk_size ||
      currentChunkOverlap !== currentIndexParameters.chunk_overlap
    ) {
      documentsNeedReindexing = true
      updateIndexingButtonState()
    } else {
      documentsNeedReindexing = false
      updateIndexingButtonState()
    }
  }

  chunkSizeInput.addEventListener('change', checkParameterChange)
  chunkOverlapInput.addEventListener('change', checkParameterChange)
  chunkSizeInput.addEventListener('input', checkParameterChange)
  chunkOverlapInput.addEventListener('input', checkParameterChange)
}

function updateIndexingButtonState () {
  const button = document.getElementById('startIndexingBtn')
  if (documentsNeedReindexing && selectedDocuments.size > 0) {
    button.innerHTML = 'Re-index Documents'
    button.style.background =
      'linear-gradient(135deg, #f56565 0%, #e53e3e 100%)'
  } else {
    button.innerHTML = 'Start Indexing'
    button.style.background =
      'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
  }
}

function showNotification (message, type) {
  const notification = document.createElement('div')
  notification.className = `notification ${type}`
  notification.textContent = message
  document.body.appendChild(notification)
  setTimeout(() => notification.remove(), 4000)
}

function handleFileSelect (event) {
  const files = event.target.files
  uploadFiles(files)
}

function handleDragOver (event) {
  event.preventDefault()
  event.currentTarget.classList.add('drag-over')
}

function handleDragLeave (event) {
  event.currentTarget.classList.remove('drag-over')
}

function handleDrop (event) {
  event.preventDefault()
  event.currentTarget.classList.remove('drag-over')
  const files = event.dataTransfer.files
  uploadFiles(files)
}

async function uploadFiles (files) {
  for (const file of files) {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      showNotification(`${file.name} is not a PDF file`, 'error')
      continue
    }

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData
      })

      if (response.ok) {
        const result = await response.json()
        showNotification(`${file.name} uploaded successfully`, 'success')
        loadDocuments()
      } else {
        const error = await response.json()
        showNotification(`Upload failed: ${error.detail}`, 'error')
      }
    } catch (error) {
      showNotification(`Upload error: ${error.message}`, 'error')
    }
  }
}

async function loadDocuments () {
  try {
    const response = await fetch(`${API_BASE}/documents`)
    const data = await response.json()
    displayDocuments(data.documents)
  } catch (error) {
    console.error('Error loading documents:', error)
    showNotification('Failed to load documents', 'error')
  }
}

function displayDocuments (documents) {
  const container = document.getElementById('documentList')

  if (documents.length === 0) {
    container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📄</div>
                <p>No documents uploaded yet</p>
            </div>
        `
    return
  }

  container.innerHTML = documents
    .map(
      doc => `
        <div class="document-item ${
          selectedDocuments.has(doc.id) ? 'selected' : ''
        }" 
                data-doc-id="${doc.id}">
            <input type="checkbox" class="document-checkbox" 
                    ${selectedDocuments.has(doc.id) ? 'checked' : ''}
                    onchange="toggleDocumentSelection('${doc.id}')">
            <div class="document-info">
                <div class="document-name">${doc.filename}</div>
                <div class="document-meta">
                    Uploaded: ${new Date(doc.uploaded_at).toLocaleDateString()}
                </div>
            </div>
            <span class="status-badge status-${doc.status}">${doc.status}</span>
            <button class="btn btn-danger" onclick="deleteDocument('${
              doc.id
            }')">
                Delete
            </button>
        </div>
    `
    )
    .join('')
}

function toggleDocumentSelection (docId) {
  const item = document.querySelector(`[data-doc-id="${docId}"]`)
  if (selectedDocuments.has(docId)) {
    selectedDocuments.delete(docId)
    item.classList.remove('selected')
  } else {
    selectedDocuments.add(docId)
    item.classList.add('selected')
  }
  updateIndexingButtonState()
}

async function deleteDocument (docId) {
  if (!confirm('Are you sure you want to delete this document?')) return

  try {
    const response = await fetch(`${API_BASE}/documents/${docId}`, {
      method: 'DELETE'
    })

    if (response.ok) {
      showNotification('Document deleted successfully', 'success')
      selectedDocuments.delete(docId)
      loadDocuments()
    } else {
      const error = await response.json()
      showNotification(`Delete failed: ${error.detail}`, 'error')
    }
  } catch (error) {
    showNotification(`Delete error: ${error.message}`, 'error')
  }
}

async function startIndexing () {
  const selected = Array.from(selectedDocuments)

  if (selected.length === 0) {
    showNotification('Please select at least one document to index', 'error')
    return
  }

  const chunkSize = parseInt(document.getElementById('chunkSize').value)
  const chunkOverlap = parseInt(document.getElementById('chunkOverlap').value)

  // Validate parameters
  if (chunkSize < 100 || chunkSize > 2000) {
    showNotification('Chunk size must be between 100 and 2000', 'error')
    return
  }

  if (chunkOverlap < 0 || chunkOverlap > 500) {
    showNotification('Chunk overlap must be between 0 and 500', 'error')
    return
  }

  if (chunkOverlap >= chunkSize) {
    showNotification('Chunk overlap must be less than chunk size', 'error')
    return
  }

  const button = document.getElementById('startIndexingBtn')

  // Show loading state
  button.disabled = true
  button.innerHTML = '<span class="loading"></span>Processing...'

  if (documentsNeedReindexing) {
    showNotification('Re-indexing with new parameters...', 'info')
  } else {
    showNotification('Starting indexing process...', 'info')
  }

  try {
    const response = await fetch(`${API_BASE}/index`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        document_ids: selected,
        chunk_size: chunkSize,
        chunk_overlap: chunkOverlap
      })
    })

    if (response.ok) {
      const result = await response.json()
      showNotification(result.message, 'success')

      // Update current parameters
      currentIndexParameters = {
        chunk_size: chunkSize,
        chunk_overlap: chunkOverlap
      }
      documentsNeedReindexing = false

      loadDocuments()
    } else {
      const error = await response.json()
      showNotification(`Indexing failed: ${error.detail}`, 'error')
    }
  } catch (error) {
    showNotification(`Indexing error: ${error.message}`, 'error')
  } finally {
    button.disabled = false
    updateIndexingButtonState()
  }
}

async function submitQuery () {
  const query = document.getElementById('queryInput').value.trim()
  if (!query) {
    showNotification('Please enter a query', 'error')
    return
  }

  const button = document.getElementById('submitQueryBtn')
  const k = parseInt(document.getElementById('kValue').value)
  const expandQuery = document.getElementById('expandQuery').checked

  // Validate k value
  if (k < 1 || k > 20) {
    showNotification('k value must be between 1 and 20', 'error')
    return
  }

  // Show loading state
  button.disabled = true
  button.innerHTML = '<span class="loading"></span>Processing...'

  const queryType = expandQuery
    ? 'with query expansion'
    : 'without query expansion'
  showNotification(`Searching for answers ${queryType} (k=${k})...`, 'info')

  try {
    const response = await fetch(`${API_BASE}/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: query,
        k: k,
        expand_query: expandQuery
      })
    })

    if (response.ok) {
      const result = await response.json()
      displayQueryResult(result, { k, expandQuery })
      showNotification('Query processed successfully!', 'success')
    } else {
      const error = await response.json()
      showNotification(`Query failed: ${error.detail}`, 'error')
    }
  } catch (error) {
    showNotification(`Query error: ${error.message}`, 'error')
  } finally {
    button.disabled = false
    button.innerHTML = 'Submit Query'
  }
}

function displayQueryResult (result, queryParams) {
  const resultsSection = document.getElementById('queryResults')
  const resultsContent = document.getElementById('resultsContent')

  // Display query parameters used
  const parametersSummary = `
        <div class="parameter-info">
            <strong>Query Parameters:</strong> 
            Retrieved ${queryParams.k} documents${
    queryParams.expandQuery
      ? ' with query expansion'
      : ' without query expansion'
  }
        </div>
    `

  let expandedQueriesHtml = ''
  if (result.expanded_queries && result.expanded_queries.length > 0) {
    expandedQueriesHtml = `
            <div class="expanded-queries">
                <h4>Expanded Queries (${
                  result.expanded_queries.length
                } variations)</h4>
                ${result.expanded_queries
                  .map(
                    q => `
                    <div class="expanded-query">${q}</div>
                `
                  )
                  .join('')}
            </div>
        `
  }

  const formattedAnswer = marked.parse(result.answer)

  resultsContent.innerHTML = `
        ${parametersSummary}
        ${expandedQueriesHtml}
        <div class="answer-section">
            <h3>Answer</h3>
            <div class="answer-text">${formattedAnswer}</div>
        </div>
    `

  resultsSection.style.display = 'block'
  resultsSection.scrollIntoView({ behavior: 'smooth' })
}
