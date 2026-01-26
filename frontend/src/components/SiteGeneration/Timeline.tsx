import React from 'react';
import { CheckCircle2, Circle, Clock, ArrowRight, FileText } from 'lucide-react';
import { motion } from 'framer-motion';

interface Step {
    id: string;
    title: string;
    description: string;
    status: 'pending' | 'active' | 'completed';
    date?: string;
}

interface TimelineProps {
    steps: Step[];
    currentStepId: string;
    onViewArtifact?: (stepId: string) => void;
}

export function Timeline({ steps, currentStepId, onViewArtifact }: TimelineProps) {
    return (
        <div className="w-full max-w-2xl mx-auto py-8">
            <div className="relative">
                {/* Vertical Line */}
                <div className="absolute left-6 top-4 bottom-4 w-0.5 bg-gray-200 dark:bg-gray-800" />

                <div className="space-y-8">
                    {steps.map((step, index) => {
                        const isActive = step.status === 'active';
                        const isCompleted = step.status === 'completed';
                        const isPending = step.status === 'pending';

                        return (
                            <motion.div
                                key={step.id}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: index * 0.1 }}
                                className={`relative flex items-start group ${isPending ? 'opacity-50' : ''}`}
                            >
                                {/* Icon */}
                                <div className={`
                  relative z-10 flex items-center justify-center w-12 h-12 rounded-full border-4 
                  ${isCompleted ? 'bg-green-100 border-green-500 text-green-600' : ''}
                  ${isActive ? 'bg-blue-100 border-blue-500 text-blue-600' : ''}
                  ${isPending ? 'bg-gray-100 border-gray-300 text-gray-400' : ''}
                  transition-colors duration-300
                `}>
                                    {isCompleted && <CheckCircle2 className="w-6 h-6" />}
                                    {isActive && <Clock className="w-6 h-6 animate-pulse" />}
                                    {isPending && <Circle className="w-6 h-6" />}
                                </div>

                                {/* Content */}
                                <div className="ml-6 flex-1 pt-2">
                                    <div className="flex items-center justify-between mb-1">
                                        <h3 className={`text-lg font-semibold ${isActive ? 'text-blue-600' : 'text-gray-900 dark:text-gray-100'}`}>
                                            {step.title}
                                        </h3>
                                        {step.date && <span className="text-sm text-gray-500">{step.date}</span>}
                                    </div>

                                    <p className="text-gray-600 dark:text-gray-400 mb-3">
                                        {step.description}
                                    </p>

                                    {/* Actions */}
                                    {(isCompleted || isActive) && onViewArtifact && (
                                        <button
                                            onClick={() => onViewArtifact(step.id)}
                                            className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-blue-600 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
                                        >
                                            <FileText className="w-4 h-4 mr-1.5" />
                                            Ver Detalhes
                                            <ArrowRight className="w-4 h-4 ml-1" />
                                        </button>
                                    )}
                                </div>
                            </motion.div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}
