"use client";

import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { mediaApi, type Episode } from "@/lib/api/media";
import { X, ChevronDown, ChevronRight, Film } from "lucide-react";

interface MediaDetailModalProps {
  mediaId: string;
  mediaTitle: string;
  isOpen: boolean;
  onClose: () => void;
}

interface SeasonGroup {
  seasonNumber: number;
  episodes: Episode[];
}

export default function MediaDetailModal({
  mediaId,
  mediaTitle,
  isOpen,
  onClose,
}: MediaDetailModalProps) {
  const [expandedSeasons, setExpandedSeasons] = useState<Set<number>>(new Set());
  const [expandedEpisodes, setExpandedEpisodes] = useState<Set<string>>(new Set());

  const { data, isLoading } = useQuery({
    queryKey: ["media-episodes", mediaId],
    queryFn: () => mediaApi.getMediaEpisodes(mediaId),
    enabled: isOpen,
  });

  // Group episodes by season
  const seasonGroups: SeasonGroup[] = data?.episodes
    ? Object.values(
        data.episodes.reduce((acc, episode) => {
          const seasonNum = episode.season_number ?? 0;
          if (!acc[seasonNum]) {
            acc[seasonNum] = {
              seasonNumber: seasonNum,
              episodes: [],
            };
          }
          acc[seasonNum].episodes.push(episode);
          return acc;
        }, {} as Record<number, SeasonGroup>)
      ).sort((a, b) => a.seasonNumber - b.seasonNumber)
    : [];

  // Intelligent default expansion logic
  useEffect(() => {
    if (!data?.episodes || expandedSeasons.size > 0) return;

    const newExpandedSeasons = new Set<number>();
    
    // Find which seasons have episodes
    const seasonsWithEpisodes = seasonGroups.map(s => s.seasonNumber);
    
    if (seasonsWithEpisodes.length > 0) {
      // Expand all watched/partially watched seasons
      seasonGroups.forEach(season => {
        if (season.episodes.length > 0) {
          newExpandedSeasons.add(season.seasonNumber);
        }
      });
      
      // If all seasons are watched, keep them all expanded
      // Otherwise, also expand the next unwatched season
      // (For now, we expand all seasons since we only track watched episodes)
    }
    
    setExpandedSeasons(newExpandedSeasons);
  }, [data, seasonGroups, expandedSeasons.size]);

  // Handle ESC key and outside click
  useEffect(() => {
    if (!isOpen) return;

    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };

    document.addEventListener("keydown", handleEsc);
    return () => document.removeEventListener("keydown", handleEsc);
  }, [isOpen, onClose]);

  const toggleSeason = (seasonNumber: number) => {
    const newExpanded = new Set(expandedSeasons);
    if (newExpanded.has(seasonNumber)) {
      newExpanded.delete(seasonNumber);
    } else {
      newExpanded.add(seasonNumber);
    }
    setExpandedSeasons(newExpanded);
  };

  const toggleEpisode = (episodeId: string) => {
    const newExpanded = new Set(expandedEpisodes);
    if (newExpanded.has(episodeId)) {
      newExpanded.delete(episodeId);
    } else {
      newExpanded.add(episodeId);
    }
    setExpandedEpisodes(newExpanded);
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm animate-in fade-in duration-200"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-4xl max-h-[90vh] bg-white dark:bg-gray-900 rounded-lg shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 z-10 bg-gradient-to-r from-purple-600 to-blue-600 dark:from-purple-900 dark:to-blue-900 text-white p-6">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-2 rounded-full hover:bg-white/20 transition-colors"
            aria-label="Close"
          >
            <X className="w-6 h-6" />
          </button>
          
          <div className="flex gap-6">
            {/* Placeholder Image */}
            <div className="flex-shrink-0 w-32 h-48 bg-white/10 rounded-lg flex items-center justify-center border-2 border-white/20">
              <Film className="w-12 h-12 text-white/50" />
            </div>
            
            {/* Series Info */}
            <div className="flex-1 flex flex-col justify-center">
              <h2 className="text-3xl font-bold mb-2">{mediaTitle}</h2>
              <div className="space-y-1 text-white/90">
                <p className="text-lg">
                  <span className="font-semibold">Type:</span> TV Series
                </p>
                <p className="text-lg">
                  <span className="font-semibold">Episodes Watched:</span>{" "}
                  {data?.total_episodes ?? 0}
                </p>
                <p className="text-lg">
                  <span className="font-semibold">Seasons:</span>{" "}
                  {seasonGroups.length}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="overflow-y-auto max-h-[calc(90vh-240px)] p-6">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
            </div>
          ) : seasonGroups.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              No episodes found
            </div>
          ) : (
            <div className="space-y-4">
              {seasonGroups.map((season) => (
                <div
                  key={season.seasonNumber}
                  className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden transition-all"
                >
                  {/* Season Header */}
                  <button
                    onClick={() => toggleSeason(season.seasonNumber)}
                    className="w-full flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-750 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      {expandedSeasons.has(season.seasonNumber) ? (
                        <ChevronDown className="w-5 h-5 text-purple-600" />
                      ) : (
                        <ChevronRight className="w-5 h-5 text-gray-400" />
                      )}
                      <span className="font-semibold text-lg">
                        Season {season.seasonNumber}
                      </span>
                      <span className="text-sm text-gray-500">
                        ({season.episodes.length} episodes)
                      </span>
                    </div>
                  </button>

                  {/* Episodes List */}
                  {expandedSeasons.has(season.seasonNumber) && (
                    <div className="divide-y divide-gray-200 dark:divide-gray-700">
                      {season.episodes.map((episode, idx) => {
                        const episodeId = `${season.seasonNumber}-${idx}`;
                        const isExpanded = expandedEpisodes.has(episodeId);

                        return (
                          <div key={episode.id} className="bg-white dark:bg-gray-900">
                            {/* Episode Header */}
                            <button
                              onClick={() => toggleEpisode(episodeId)}
                              className="w-full flex items-start gap-3 p-4 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors text-left"
                            >
                              <div className="flex-shrink-0 mt-0.5">
                                {isExpanded ? (
                                  <ChevronDown className="w-4 h-4 text-purple-600" />
                                ) : (
                                  <ChevronRight className="w-4 h-4 text-gray-400" />
                                )}
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-1">
                                  <span className="font-mono text-sm text-purple-600 dark:text-purple-400 font-semibold">
                                    E{episode.episode_number ?? idx + 1}
                                  </span>
                                  <span className="font-medium truncate">
                                    {episode.episode_title || "Untitled Episode"}
                                  </span>
                                </div>
                                {episode.consumed_at && (
                                  <p className="text-xs text-gray-500">
                                    Watched on{" "}
                                    {new Date(episode.consumed_at).toLocaleDateString()}
                                  </p>
                                )}
                              </div>
                            </button>

                            {/* Episode Description (Expanded) */}
                            {isExpanded && (
                              <div className="px-4 pb-4 pl-11 animate-in slide-in-from-top-2 duration-200">
                                <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                                  <p className="text-sm text-gray-600 dark:text-gray-400 italic">
                                    Episode description placeholder. This will show
                                    episode synopsis, runtime, and other details when
                                    integrated with TMDB API.
                                  </p>
                                </div>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
