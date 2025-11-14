import React, { useState } from 'react'
import { Search, Loader2 } from 'lucide-react'
import { Button } from '../ui/Button'
import { searchApi } from '../../services/api'
import { SearchResult, SearchResponse } from '../../types/document'
import { Card, CardContent } from '../ui/Card'
import { Badge } from '../ui/Badge'
import { formatDate } from '../../lib/utils'

export const SearchBar: React.FC = () => {
  const [query, setQuery] = useState('')
  const [searchType, setSearchType] = useState<'hybrid' | 'full-text' | 'semantic'>('hybrid')
  const [results, setResults] = useState<SearchResponse | null>(null)
  const [searching, setSearching] = useState(false)

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!query.trim()) return

    setSearching(true)
    
    try {
      let response: SearchResponse
      
      switch (searchType) {
        case 'full-text':
          response = await searchApi.fullText(query)
          break
        case 'semantic':
          response = await searchApi.semantic(query)
          break
        default:
          response = await searchApi.hybrid(query)
      }
      
      setResults(response)
    } catch (error) {
      console.error('Search failed:', error)
      alert('Search failed')
    } finally {
      setSearching(false)
    }
  }

  return (
    <div className="space-y-4">
      <form onSubmit={handleSearch} className="space-y-3">
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search documents..."
              className="w-full pl-10 pr-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          
          <Button type="submit" disabled={searching} size="lg">
            {searching ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Searching...
              </>
            ) : (
              <>
                <Search className="h-4 w-4 mr-2" />
                Search
              </>
            )}
          </Button>
        </div>

        {/* Search Type Selector */}
        <div className="flex gap-2">
          <Button
            type="button"
            variant={searchType === 'hybrid' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSearchType('hybrid')}
          >
            Hybrid (Best)
          </Button>
          <Button
            type="button"
            variant={searchType === 'full-text' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSearchType('full-text')}
          >
            Keyword
          </Button>
          <Button
            type="button"
            variant={searchType === 'semantic' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSearchType('semantic')}
          >
            Semantic
          </Button>
        </div>
      </form>

      {/* Search Results */}
      {results && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium">
              {results.total} results for "{results.query}"
            </h3>
            <Badge variant="outline">{results.search_type}</Badge>
          </div>

          {results.results.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center text-gray-500">
                No documents found
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-2">
              {results.results.map((result) => (
                <Card key={result.id} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <h4 className="font-medium">{result.original_filename}</h4>
                        <p className="text-sm text-gray-500">{formatDate(result.created_at)}</p>
                      </div>
                      
                      <div className="flex gap-2">
                        <Badge variant="outline">{result.document_type}</Badge>
                        {result.score && (
                          <Badge variant="secondary">
                            {(result.score * 100).toFixed(0)}% match
                          </Badge>
                        )}
                      </div>
                    </div>

                    {result.summary && (
                      <p className="text-sm text-gray-600 mb-2">{result.summary}</p>
                    )}

                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => window.open(`/documents/${result.id}`, '_blank')}
                    >
                      View Document
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}