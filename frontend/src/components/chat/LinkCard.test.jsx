import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, test, expect, beforeEach, afterEach, vi } from 'vitest'
import LinkCard from './LinkCard.jsx'

describe('LinkCard', () => {
  beforeEach(() => {
    // Mock clipboard API
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn(() => Promise.resolve())
      }
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  test('renders title and hostname', () => {
    render(
      <LinkCard
        title="Test Document"
        url="https://example.com/path/file.pdf"
        isDownload={false}
      />
    )
    expect(screen.getByText('Test Document')).toBeInTheDocument()
    expect(screen.getByText('example.com')).toBeInTheDocument()
  })

  test('renders Open and Copy buttons for all links', () => {
    render(
      <LinkCard
        title="Test"
        url="https://example.com/file.pdf"
        isDownload={false}
      />
    )
    expect(screen.getByLabelText('Open link')).toBeInTheDocument()
    expect(screen.getByLabelText('Copy link')).toBeInTheDocument()
  })

  test('renders Download button when isDownload is true', () => {
    render(
      <LinkCard
        title="Test CSV"
        url="https://example.com/data.csv"
        isDownload={true}
      />
    )
    expect(screen.getByLabelText('Download file')).toBeInTheDocument()
  })

  test('does not render Download button when isDownload is false', () => {
    render(
      <LinkCard
        title="Test"
        url="https://example.com/page.html"
        isDownload={false}
      />
    )
    expect(screen.queryByLabelText('Download file')).not.toBeInTheDocument()
  })

  test('copies link to clipboard and shows confirmation', async () => {
    render(
      <LinkCard
        title="Test"
        url="https://example.com/file.pdf"
        isDownload={false}
      />
    )
    const copyButton = screen.getByLabelText('Copy link')
    fireEvent.click(copyButton)
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('https://example.com/file.pdf')
    await waitFor(() => {
      expect(screen.getByLabelText('Copied!')).toBeInTheDocument()
    })
    await waitFor(() => {
      expect(screen.getByLabelText('Copy link')).toBeInTheDocument()
    }, { timeout: 1500 })
  })

  test('transforms GitHub blob URL to raw URL for download', () => {
    const { container } = render(
      <LinkCard
        title="GitHub CSV"
        url="https://github.com/owner/repo/blob/abc123/data.csv"
        isDownload={true}
      />
    )
    const downloadLink = screen.getByLabelText('Download file')
    expect(downloadLink.href).toBe('https://raw.githubusercontent.com/owner/repo/abc123/data.csv')
    expect(downloadLink).toHaveAttribute('download')
  })

  test('renders icons with correct accessibility labels', () => {
    const testCases = [
      { url: 'file.pdf', expectedLabel: 'Type: PDF' },
      { url: 'data.csv', expectedLabel: 'Type: Spreadsheet' },
      { url: 'data.json', expectedLabel: 'Type: JSON' },
      { url: 'archive.zip', expectedLabel: 'Type: Archive' },
      { url: 'page.html', expectedLabel: 'Type: Web Page' },
      { url: 'page.txt', expectedLabel: 'Type: Document' }
    ]
    testCases.forEach(({ url, expectedLabel }) => {
      const { unmount } = render(
        <LinkCard
          title="Test"
          url={`https://example.com/${url}`}
          isDownload={false}
        />
      )
      const icon = screen.getByLabelText(expectedLabel)
      expect(icon).toBeInTheDocument()
      unmount()
    })
  })

  test('renders globe icon for links without file extensions', () => {
    render(
      <LinkCard
        title="Website"
        url="https://example.com"
        isDownload={false}
      />
    )
    const icon = screen.getByLabelText('Type: Link')
    expect(icon).toBeInTheDocument()
  })

  test('renders generic file icon for unknown extensions', () => {
    render(
      <LinkCard
        title="Unknown File"
        url="https://example.com/file.xyz"
        isDownload={false}
      />
    )
    const icon = screen.getByLabelText('Type: File')
    expect(icon).toBeInTheDocument()
  })

  test('handles missing title by showing URL', () => {
    render(
      <LinkCard
        url="https://example.com/document.pdf"
        isDownload={false}
      />
    )
    expect(screen.getByText('https://example.com/document.pdf')).toBeInTheDocument()
  })

  test('opens link in new tab with correct attributes', () => {
    render(
      <LinkCard
        title="Test"
        url="https://example.com/file.pdf"
        isDownload={false}
      />
    )
    const openLink = screen.getByLabelText('Open link')
    expect(openLink).toHaveAttribute('href', 'https://example.com/file.pdf')
    expect(openLink).toHaveAttribute('target', '_blank')
    expect(openLink).toHaveAttribute('rel', 'noreferrer')
  })

  test('does not show Preview button for external links', () => {
    render(
      <LinkCard
        title="External"
        url="https://external-domain.com/file.pdf"
        isDownload={false}
      />
    )
    expect(screen.queryByLabelText('Preview document')).not.toBeInTheDocument()
  })

  test('handles GitHub URLs with nested paths', () => {
    render(
      <LinkCard
        title="Deep File"
        url="https://github.com/owner/repo/blob/main/src/data/nested/file.csv"
        isDownload={true}
      />
    )
    const downloadLink = screen.getByLabelText('Download file')
    expect(downloadLink.href).toBe('https://raw.githubusercontent.com/owner/repo/main/src/data/nested/file.csv')
  })

  test('preserves non-GitHub download URLs unchanged', () => {
    render(
      <LinkCard
        title="External File"
        url="https://example.com/data/file.csv"
        isDownload={true}
      />
    )
    const downloadLink = screen.getByLabelText('Download file')
    expect(downloadLink.href).toBe('https://example.com/data/file.csv')
  })
})
