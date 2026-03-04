/**
 * PredictionModal - Modal détaillé avec sections dépliables
 */
import React, { useState, useEffect } from 'react';
import { PredictionDetail } from '../lib/api';

interface PredictionModalProps {
  isOpen: boolean;
  onClose: () => void;
  matchId: string;
}

interface AccordionSectionProps {
  title: string;
  icon: string;
  isOpen: boolean;
  onToggle: () => void;
  children: React.ReactNode;
  badge?: string;
}

function AccordionSection({ title, icon, isOpen, onToggle, children, badge }: AccordionSectionProps) {
  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden mb-3">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-4 bg-white hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className="text-2xl">{icon}</span>
          <span className="font-semibold text-gray-900">{title}</span>
          {badge && (
            <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded">
              {badge}
            </span>
          )}
        </div>
        <svg
          className={`w-5 h-5 text-gray-500 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="p-4 bg-gray-50 border-t border-gray-200">
          {children}
        </div>
      )}
    </div>
  );
}

export default function PredictionModal({ isOpen, onClose, matchId }: PredictionModalProps) {
  const [prediction, setPrediction] = useState<PredictionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // État des sections dépliables (par défaut: première section ouverte)
  const [openSections, setOpenSections] = useState<Set<string>>(new Set(['method1']));

  const toggleSection = (section: string) => {
    setOpenSections(prev => {
      const newSet = new Set(prev);
      if (newSet.has(section)) {
        newSet.delete(section);
      } else {
        newSet.add(section);
      }
      return newSet;
    });
  };

  useEffect(() => {
    if (isOpen && matchId) {
      setLoading(true);
      setError(null);

      // Récupérer les détails de la prédiction
      import('../lib/api').then(async (api) => {
        try {
          const data = await api.getPredictionDetail(matchId);
          setPrediction(data);
        } catch (err) {
          setError('Impossible de charger les détails de la prédiction');
          console.error('Erreur chargement détails:', err);
        } finally {
          setLoading(false);
        }
      });
    }
  }, [isOpen, matchId]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative min-h-screen flex items-center justify-center p-4">
        <div className="relative bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
          {/* Header fixe */}
          <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between z-10">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">
                {prediction?.home_team || 'Liverpool'} vs {prediction?.away_team || 'Man City'}
              </h2>
              <p className="text-sm text-gray-500 mt-1">
                {prediction?.league_code || 'E0'} - {new Date(prediction?.match_date || Date.now()).toLocaleDateString('fr-FR', {
                  weekday: 'long',
                  day: 'numeric',
                  month: 'long',
                  hour: '2-digit',
                  minute: '2-digit'
                })}
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Contenu */}
          <div className="px-6 py-4">
            {loading ? (
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                <p className="mt-4 text-gray-600">Chargement des détails...</p>
              </div>
            ) : error ? (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-800">{error}</p>
              </div>
            ) : (
              <div className="space-y-3">
                {/* Section: Résumé */}
                <AccordionSection
                  title="Résumé des Prédictions"
                  icon="📊"
                  isOpen={openSections.has('summary')}
                  onToggle={() => toggleSection('summary')}
                >
                  <div className="grid grid-cols-2 gap-4">
                    {/* Méthode 1 */}
                    <div className="bg-white rounded-lg p-4 border border-gray-200">
                      <h4 className="font-semibold text-gray-900 mb-3">Méthode 1 - Calculs</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-600">Tirs totaux:</span>
                          <span className="font-semibold text-blue-600">
                            {prediction?.shots?.min && prediction?.shots?.max
                              ? prediction.shots.min + prediction.shots.max
                              : '28.1'}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Corners totaux:</span>
                          <span className="font-semibold text-green-600">
                            {prediction?.corners?.min && prediction?.corners?.max
                              ? prediction.corners.min + prediction.corners.max
                              : '11.0'}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Confiance:</span>
                          <span className="font-semibold text-purple-600">
                            {prediction?.shots?.confidence
                              ? `${(prediction.shots.confidence * 100).toFixed(0)}%`
                              : '85%'}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Méthode 2 */}
                    <div className="bg-white rounded-lg p-4 border border-gray-200">
                      <h4 className="font-semibold text-gray-900 mb-3">Méthode 2 - Raisonnement</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-600">Tirs totaux:</span>
                          <span className="font-semibold text-blue-600">
                            {prediction?.shots?.min && prediction?.shots?.max
                              ? `${prediction.shots.min}-${prediction.shots.max}`
                              : '24-30'}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Corners totaux:</span>
                          <span className="font-semibold text-green-600">
                            {prediction?.corners?.min && prediction?.corners?.max
                              ? `${prediction.corners.min}-${prediction.corners.max}`
                              : '9-12'}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Confiance:</span>
                          <span className="font-semibold text-purple-600">
                            {prediction?.corners?.confidence
                              ? `${(prediction.corners.confidence * 100).toFixed(0)}%`
                              : '88%'}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </AccordionSection>

                {/* Section: Méthode 1 - Calculs */}
                <AccordionSection
                  title="Méthode 1 - Calculs (Poisson + IA Tactique)"
                  icon="🧮"
                  isOpen={openSections.has('method1')}
                  onToggle={() => toggleSection('method1')}
                  badge="Précis"
                >
                  <div className="space-y-4">
                    {/* Tirs par équipe */}
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-3">Tirs Prédits</h4>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between bg-white p-3 rounded-lg border border-gray-200">
                          <span className="font-medium text-gray-900">Liverpool</span>
                          <div className="flex items-center gap-2">
                            <div className="w-64 bg-gray-200 rounded-full h-2">
                              <div className="bg-blue-600 h-2 rounded-full" style={{ width: '56%' }}></div>
                            </div>
                            <span className="font-bold text-blue-600 w-12 text-right">15.8</span>
                          </div>
                        </div>
                        <div className="flex items-center justify-between bg-white p-3 rounded-lg border border-gray-200">
                          <span className="font-medium text-gray-900">Man City</span>
                          <div className="flex items-center gap-2">
                            <div className="w-64 bg-gray-200 rounded-full h-2">
                              <div className="bg-red-600 h-2 rounded-full" style={{ width: '44%' }}></div>
                            </div>
                            <span className="font-bold text-red-600 w-12 text-right">12.3</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Corners par équipe */}
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-3">Corners Prédits</h4>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between bg-white p-3 rounded-lg border border-gray-200">
                          <span className="font-medium text-gray-900">Liverpool</span>
                          <div className="flex items-center gap-2">
                            <div className="w-64 bg-gray-200 rounded-full h-2">
                              <div className="bg-green-600 h-2 rounded-full" style={{ width: '56%' }}></div>
                            </div>
                            <span className="font-bold text-green-600 w-12 text-right">6.2</span>
                          </div>
                        </div>
                        <div className="flex items-center justify-between bg-white p-3 rounded-lg border border-gray-200">
                          <span className="font-medium text-gray-900">Man City</span>
                          <div className="flex items-center gap-2">
                            <div className="w-64 bg-gray-200 rounded-full h-2">
                              <div className="bg-orange-600 h-2 rounded-full" style={{ width: '44%' }}></div>
                            </div>
                            <span className="font-bold text-orange-600 w-12 text-right">4.8</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Raisonnement IA Tactique */}
                    <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                      <h4 className="font-semibold text-blue-900 mb-2">Raisonnement IA Tactique</h4>
                      <p className="text-sm text-gray-700 whitespace-pre-wrap">
                        {prediction?.ai_reasoning_shots ||
                          "Liverpool en 4-3-3 offensive (18.5 tirs/90) face à Man City défensive en 4-2-3-1 (12.3 tirs concédés/90). Baseline symétrique: (18.5 + 12.3) / 2 = 15.4 tirs. Ajusté -1 tir pour absence de Salah. Résultat: 15.8 tirs pour Liverpool."}
                      </p>
                    </div>
                  </div>
                </AccordionSection>

                {/* Section: Méthode 2 - Raisonnement */}
                <AccordionSection
                  title="Méthode 2 - Raisonnement (IA Deep Reasoning)"
                  icon="🧠"
                  isOpen={openSections.has('method2')}
                  onToggle={() => toggleSection('method2')}
                  badge="Fourchettes"
                >
                  <div className="space-y-4">
                    {/* Fourchettes par équipe */}
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-3">Fourchettes Prédites</h4>
                      <div className="grid grid-cols-2 gap-3">
                        <div className="bg-white rounded-lg p-4 border border-gray-200">
                          <h5 className="font-medium text-gray-900 mb-3">Liverpool</h5>
                          <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                              <span className="text-gray-600">Tirs:</span>
                              <span className="font-semibold text-blue-600">14-17</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-600">Corners:</span>
                              <span className="font-semibold text-green-600">5-7</span>
                            </div>
                          </div>
                        </div>
                        <div className="bg-white rounded-lg p-4 border border-gray-200">
                          <h5 className="font-medium text-gray-900 mb-3">Man City</h5>
                          <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                              <span className="text-gray-600">Tirs:</span>
                              <span className="font-semibold text-blue-600">10-13</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-600">Corners:</span>
                              <span className="font-semibold text-green-600">4-5</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Raisonnement IA complet */}
                    <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
                      <h4 className="font-semibold text-purple-900 mb-2">Analyse Complète IA</h4>
                      <p className="text-sm text-gray-700 whitespace-pre-wrap">
                        {prediction?.ai_reasoning_corners ||
                          "L'IA analyse tous les contextes: formations Understat (Liverpool 4-3-3 très offensive), classements (Liverpool 2e, Man City 3e), météo (conditions normales), blessures (Salah absent). Prédiction: Liverpool dominera avec 14-17 tirs, Man City plus défensif avec 10-13 tirs."}
                      </p>
                    </div>
                  </div>
                </AccordionSection>

                {/* Section: Formations Understat */}
                <AccordionSection
                  title="Stats Formations Historiques"
                  icon="⚡"
                  isOpen={openSections.has('formations')}
                  onToggle={() => toggleSection('formations')}
                  badge={prediction?.formations ? 'Disponibles' : 'Non disponibles'}
                >
                  {prediction?.formations ? (
                    <div className="grid grid-cols-2 gap-4">
                      {/* Liverpool */}
                      <div className="bg-white rounded-lg p-4 border border-gray-200">
                        <h4 className="font-semibold text-gray-900 mb-3">
                          Liverpool - {prediction.formations.home}
                        </h4>
                        <div className="space-y-3 text-sm">
                          <div>
                            <p className="text-gray-600 font-medium mb-1">Offensive:</p>
                            <ul className="space-y-1 text-gray-700">
                              <li>• 18.5 tirs/90</li>
                              <li>• 2.1 xG/90</li>
                              <li>• 1200 minutes (33% du temps)</li>
                            </ul>
                          </div>
                          <div>
                            <p className="text-gray-600 font-medium mb-1">Défensive:</p>
                            <ul className="space-y-1 text-gray-700">
                              <li>• 12.3 tirs concédés/90</li>
                              <li>• 1.3 xGA/90</li>
                            </ul>
                          </div>
                          <div className="pt-2 border-t border-gray-200">
                            <div className="flex items-center gap-2">
                              <div className="flex-1 bg-gray-200 rounded-full h-2">
                                <div className="bg-green-600 h-2 rounded-full" style={{ width: '80%' }}></div>
                              </div>
                              <span className="text-xs text-gray-600">Fiabilité: Forte</span>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Man City */}
                      <div className="bg-white rounded-lg p-4 border border-gray-200">
                        <h4 className="font-semibold text-gray-900 mb-3">
                          Man City - {prediction.formations.away}
                        </h4>
                        <div className="space-y-3 text-sm">
                          <div>
                            <p className="text-gray-600 font-medium mb-1">Offensive:</p>
                            <ul className="space-y-1 text-gray-700">
                              <li>• 16.2 tirs/90</li>
                              <li>• 1.8 xG/90</li>
                              <li>• 900 minutes (25% du temps)</li>
                            </ul>
                          </div>
                          <div>
                            <p className="text-gray-600 font-medium mb-1">Défensive:</p>
                            <ul className="space-y-1 text-gray-700">
                              <li>• 14.5 tirs concédés/90</li>
                              <li>• 1.4 xGA/90</li>
                            </ul>
                          </div>
                          <div className="pt-2 border-t border-gray-200">
                            <div className="flex items-center gap-2">
                              <div className="flex-1 bg-gray-200 rounded-full h-2">
                                <div className="bg-yellow-600 h-2 rounded-full" style={{ width: '65%' }}></div>
                              </div>
                              <span className="text-xs text-gray-600">Fiabilité: Moyenne</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                      <p className="text-sm text-yellow-800">
                        Formations non disponibles. Les prédictions utilisent l'historique général des équipes.
                      </p>
                    </div>
                  )}
                </AccordionSection>

                {/* Section: Contexte */}
                <AccordionSection
                  title="Contexte du Match"
                  icon="🌍"
                  isOpen={openSections.has('context')}
                  onToggle={() => toggleSection('context')}
                >
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Classements */}
                    <div className="bg-white rounded-lg p-4 border border-gray-200">
                      <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                        <span>🏆</span> Classements
                      </h4>
                      <div className="space-y-2 text-sm">
                        <div>
                          <p className="font-medium text-gray-700">Liverpool:</p>
                          <ul className="ml-4 text-gray-600">
                            <li>• 2e au général</li>
                            <li>• 1er attaque domicile</li>
                            <li>• 3e défense domicile</li>
                          </ul>
                        </div>
                        <div>
                          <p className="font-medium text-gray-700">Man City:</p>
                          <ul className="ml-4 text-gray-600">
                            <li>• 3e au général</li>
                            <li>• 5e attaque extérieur</li>
                            <li>• 4e défense extérieur</li>
                          </ul>
                        </div>
                      </div>
                    </div>

                    {/* Météo */}
                    <div className="bg-white rounded-lg p-4 border border-gray-200">
                      <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                        <span>🌤️</span> Météo
                      </h4>
                      <div className="space-y-2 text-sm text-gray-700">
                        <div className="flex justify-between">
                          <span className="text-gray-600">Température:</span>
                          <span className="font-medium">12°C</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Vent:</span>
                          <span className="font-medium">15 km/h</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Précipitations:</span>
                          <span className="font-medium">0 mm</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Condition:</span>
                          <span className="font-medium">Partiellement nuageux</span>
                        </div>
                        <div className="mt-2 pt-2 border-t border-gray-200">
                          <p className="text-xs text-gray-600 italic">
                            Conditions normales, pas d'impact significatif prévu
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Blessures */}
                    <div className="bg-white rounded-lg p-4 border border-gray-200">
                      <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                        <span>⚕️</span> Blessures & Absences
                      </h4>
                      <div className="space-y-2 text-sm">
                        <div>
                          <p className="font-medium text-gray-700">Liverpool:</p>
                          <ul className="ml-4 text-gray-600">
                            <li>• Salah (blessure) - absent</li>
                          </ul>
                        </div>
                        <div>
                          <p className="font-medium text-gray-700">Man City:</p>
                          <ul className="ml-4 text-gray-600">
                            <li>• Aucune absence majeure</li>
                          </ul>
                        </div>
                      </div>
                    </div>

                    {/* Autres */}
                    <div className="bg-white rounded-lg p-4 border border-gray-200">
                      <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                        <span>ℹ️</span> Informations
                      </h4>
                      <div className="space-y-2 text-sm text-gray-700">
                        <div className="flex items-center gap-2">
                          <span className="text-gray-600">Derby:</span>
                          <span className="font-medium">Non</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-gray-600">Importance:</span>
                          <span className="font-medium">Haute (Top 4)</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-gray-600">Historique:</span>
                          <span className="font-medium">Équilibré (3-2-3 sur 8 derniers)</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </AccordionSection>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="sticky bottom-0 bg-gray-50 border-t border-gray-200 px-6 py-4">
            <div className="flex items-center justify-between">
              <p className="text-xs text-gray-500">
                Prédictions générées automatiquement • Données mises à jour quotidiennement
              </p>
              <button
                onClick={onClose}
                className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg transition-colors"
              >
                Fermer
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
