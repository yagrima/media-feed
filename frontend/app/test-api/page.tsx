'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function TestAPIPage() {
  const [tokenResult, setTokenResult] = useState('')
  const [apiResult, setApiResult] = useState('')
  const [fetchResult, setFetchResult] = useState('')

  const checkToken = () => {
    const token = localStorage.getItem('access_token')
    
    if (token) {
      setTokenResult(`✓ Token found: ${token.substring(0, 50)}...\nLength: ${token.length}`)
    } else {
      setTokenResult('✗ No token in localStorage!\nPlease login at http://localhost:3000/login first')
    }
  }

  const testMediaAPI = async () => {
    const token = localStorage.getItem('access_token')
    
    if (!token) {
      setApiResult('✗ No token found. Please login first.')
      return
    }

    setApiResult('Testing...')

    try {
      const response = await fetch('http://localhost:8000/api/media?page=1&limit=5', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      const data = await response.json()
      
      if (response.ok) {
        setApiResult(
          `✓ SUCCESS! Status: ${response.status}\n\n` +
          `Total items: ${data.total}\n` +
          `Items returned: ${data.items.length}\n\n` +
          `First item: ${data.items[0]?.media?.title || 'N/A'}\n\n` +
          `Full Response:\n${JSON.stringify(data, null, 2)}`
        )
      } else {
        setApiResult(`✗ API Error: ${response.status}\n\n${JSON.stringify(data, null, 2)}`)
      }
    } catch (error: any) {
      setApiResult(`✗ FETCH ERROR:\n${error.message}\n\nThis might be a CORS or network issue.`)
      console.error('Fetch error:', error)
    }
  }

  const testWithFetch = async () => {
    const token = localStorage.getItem('access_token')
    
    setFetchResult('Testing with detailed fetch...')

    try {
      console.log('Making fetch request...')
      const response = await fetch('http://localhost:8000/api/media?page=1&limit=5', {
        method: 'GET',
        mode: 'cors',
        credentials: 'include',
        headers: {
          'Authorization': `Bearer ${token || 'NO_TOKEN'}`,
          'Content-Type': 'application/json'
        }
      })

      console.log('Response received:', response)
      const data = await response.json()
      
      setFetchResult(
        `Status: ${response.status}\n` +
        `OK: ${response.ok}\n\n` +
        `Data:\n${JSON.stringify(data, null, 2)}`
      )
      
    } catch (error: any) {
      setFetchResult(
        `FETCH FAILED:\n${error.name}: ${error.message}\n\n` +
        `This suggests:\n` +
        `- CORS configuration issue\n` +
        `- Network/connection problem\n` +
        `- Backend not responding\n\n` +
        `Check browser console for details.`
      )
      console.error('Detailed error:', error)
    }
  }

  // Auto-check token on mount (client-side only)
  if (typeof window !== 'undefined') {
    useState(() => {
      checkToken()
    })
  }

  return (
    <div className="container mx-auto max-w-4xl p-6 space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold">Media API Direct Test</h1>
        <p className="text-muted-foreground">
          This page tests the /api/media endpoint directly, bypassing React Query and other framework layers.
        </p>
      </div>

      <Card className="bg-blue-50 border-blue-200">
        <CardHeader>
          <CardTitle>Instructions</CardTitle>
        </CardHeader>
        <CardContent>
          <ol className="list-decimal list-inside space-y-2">
            <li>Make sure you're logged in on http://localhost:3000/login</li>
            <li>Click the test buttons below in order</li>
            <li>Check the results</li>
          </ol>
        </CardContent>
      </Card>

      {/* Token Check */}
      <Card>
        <CardHeader>
          <CardTitle>Step 1: Check Token</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button onClick={checkToken}>Check LocalStorage Token</Button>
          {tokenResult && (
            <pre className={`p-4 rounded text-sm overflow-x-auto ${
              tokenResult.includes('✓') ? 'bg-green-50' : 'bg-red-50'
            }`}>
              {tokenResult}
            </pre>
          )}
        </CardContent>
      </Card>

      {/* API Test */}
      <Card>
        <CardHeader>
          <CardTitle>Step 2: Test Media API</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button onClick={testMediaAPI}>Test Media API</Button>
          {apiResult && (
            <pre className={`p-4 rounded text-sm overflow-x-auto ${
              apiResult.includes('✓ SUCCESS') ? 'bg-green-50' : 
              apiResult.includes('Testing') ? 'bg-blue-50' : 'bg-red-50'
            }`}>
              {apiResult}
            </pre>
          )}
        </CardContent>
      </Card>

      {/* Fetch Test */}
      <Card>
        <CardHeader>
          <CardTitle>Step 3: Test with Fetch (CORS Test)</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button onClick={testWithFetch}>Test with Fetch</Button>
          {fetchResult && (
            <pre className={`p-4 rounded text-sm overflow-x-auto ${
              fetchResult.includes('Status: 200') ? 'bg-green-50' :
              fetchResult.includes('Testing') ? 'bg-blue-50' : 'bg-red-50'
            }`}>
              {fetchResult}
            </pre>
          )}
        </CardContent>
      </Card>

      <Card className="bg-gray-50">
        <CardHeader>
          <CardTitle>Debug Info</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm">
            <p><strong>Backend URL:</strong> http://localhost:8000</p>
            <p><strong>Endpoint:</strong> /api/media?page=1&limit=5</p>
            <p><strong>Current URL:</strong> {typeof window !== 'undefined' ? window.location.href : 'N/A'}</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
