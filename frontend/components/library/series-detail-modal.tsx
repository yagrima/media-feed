"use client";

import { useEffect } from "react";
import { X, BookOpen, Calendar, Clock, Star, User } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { UserMedia } from "@/lib/api/media";

interface SeriesDetailModalProps {
  seriesTitle: string;
  books: UserMedia[];
  isOpen: boolean;
  onClose: () => void;
}

export default function SeriesDetailModal({
  seriesTitle,
  books,
  isOpen,
  onClose,
}: SeriesDetailModalProps) {
  
  // Sort books by sequence if available, otherwise by consumption date
  const sortedBooks = [...books].sort((a, b) => {
    const seqA = a.media.media_metadata?.series?.sequence;
    const seqB = b.media.media_metadata?.series?.sequence;
    
    // If both have sequence numbers, sort by them
    if (seqA && seqB) {
      const numA = parseFloat(seqA);
      const numB = parseFloat(seqB);
      if (!isNaN(numA) && !isNaN(numB)) return numA - numB;
      return seqA.localeCompare(seqB);
    }
    
    // Fallback to purchase date
    return new Date(a.consumed_at).getTime() - new Date(b.consumed_at).getTime();
  });

  const representative = sortedBooks[0];
  const author = representative.media.media_metadata?.authors?.[0] || "Unknown Author";
  const totalDuration = sortedBooks.reduce((acc, book) => acc + (book.media.media_metadata?.duration_minutes || 0), 0);
  const hours = Math.floor(totalDuration / 60);
  const minutes = totalDuration % 60;

  // Handle ESC key
  useEffect(() => {
    if (!isOpen) return;
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleEsc);
    return () => document.removeEventListener("keydown", handleEsc);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm animate-in fade-in duration-200"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-4xl max-h-[90vh] bg-white dark:bg-gray-900 rounded-lg shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200 flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 z-10 bg-gradient-to-r from-amber-600 to-orange-600 text-white p-6 shrink-0">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-2 rounded-full hover:bg-white/20 transition-colors"
            aria-label="Close"
          >
            <X className="w-6 h-6" />
          </button>
          
          <div className="flex gap-6">
            {/* Cover Image */}
            <div className="flex-shrink-0 w-32 h-32 bg-white/10 rounded-lg flex items-center justify-center border-2 border-white/20 overflow-hidden">
              {representative.media.media_metadata?.cover_url ? (
                <img 
                  src={representative.media.media_metadata.cover_url} 
                  alt={seriesTitle}
                  className="w-full h-full object-cover"
                />
              ) : (
                <BookOpen className="w-12 h-12 text-white/50" />
              )}
            </div>
            
            {/* Series Info */}
            <div className="flex-1 flex flex-col justify-center">
              <div className="flex items-center gap-2 mb-1">
                <Badge variant="secondary" className="bg-white/20 hover:bg-white/30 text-white border-0">
                  Audiobook Series
                </Badge>
              </div>
              <h2 className="text-3xl font-bold mb-2">{seriesTitle}</h2>
              <div className="space-y-1 text-white/90 flex flex-wrap gap-4 text-sm">
                <div className="flex items-center gap-1">
                  <User className="w-4 h-4 opacity-75" />
                  <span>{author}</span>
                </div>
                <div className="flex items-center gap-1">
                  <BookOpen className="w-4 h-4 opacity-75" />
                  <span>{sortedBooks.length} Books</span>
                </div>
                <div className="flex items-center gap-1">
                  <Clock className="w-4 h-4 opacity-75" />
                  <span>{hours}h {minutes}m Total</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Content - Scrollable */}
        <div className="overflow-y-auto p-6 flex-1">
          <div className="space-y-4">
            {sortedBooks.map((book) => {
              const metadata = book.media.media_metadata;
              const bookDuration = metadata?.duration_minutes || 0;
              const bookHours = Math.floor(bookDuration / 60);
              const bookMins = bookDuration % 60;
              const sequence = metadata?.series?.sequence ? `#${metadata.series.sequence}` : '';

              return (
                <div
                  key={book.id}
                  className="flex items-start gap-4 p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg border border-gray-100 dark:border-gray-700 hover:border-amber-200 dark:hover:border-amber-800 transition-colors"
                >
                  {/* Thumbnail */}
                  <div className="w-16 h-16 shrink-0 bg-gray-200 dark:bg-gray-700 rounded overflow-hidden">
                    {metadata?.cover_url ? (
                      <img src={metadata.cover_url} alt={book.media.title} className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-gray-400">
                        <BookOpen className="w-6 h-6" />
                      </div>
                    )}
                  </div>

                  {/* Details */}
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-semibold text-lg text-gray-900 dark:text-gray-100 flex items-center gap-2">
                          {sequence && <span className="text-amber-600 dark:text-amber-500 font-mono text-base">{sequence}</span>}
                          {book.media.title}
                        </h3>
                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                          {metadata?.narrators?.length ? `Narrated by ${metadata.narrators.join(", ")}` : "Unknown Narrator"}
                        </p>
                      </div>
                      {metadata?.rating && (
                        <Badge variant="outline" className="flex items-center gap-1 border-amber-200 text-amber-700 dark:text-amber-400">
                          <Star className="w-3 h-3 fill-current" />
                          {metadata.rating}
                        </Badge>
                      )}
                    </div>

                    <div className="flex items-center gap-4 mt-3 text-xs text-gray-500 dark:text-gray-400">
                      <div className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        Purchased: {new Date(book.consumed_at).toLocaleDateString()}
                      </div>
                      <div className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {bookHours}h {bookMins}m
                      </div>
                      {metadata?.publisher && (
                        <span className="hidden sm:inline-block px-2 py-0.5 bg-gray-100 dark:bg-gray-800 rounded-full">
                          {metadata.publisher}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
