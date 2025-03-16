import logging

# Cette classe est définie partiellement, 
# elle est destinée à être importée dans OBSCapture dans obs_capture.py
class OBSEventsMixin:
    """
    Mixin pour la gestion des événements OBS.
    Ces méthodes sont intégrées à la classe OBSCapture.
    """
    
    def _on_switch_scene(self, event):
        """
        Callback pour l'événement de changement de scène
        """
        scene_name = event.getSceneName()
        self.logger.info(f"Scène active changée: {scene_name}")
        self._refresh_sources()
    
    def _on_stream_starting(self, event):
        """
        Callback pour l'événement de démarrage de stream
        """
        self.logger.info("Stream en cours de démarrage")
    
    def _on_stream_stopping(self, event):
        """
        Callback pour l'événement d'arrêt de stream
        """
        self.logger.info("Stream en cours d'arrêt")
    
    def _on_media_play(self, event):
        """
        Callback pour l'événement de lecture média
        """
        source_name = event.getSourceName()
        self.logger.info(f"Média démarré: {source_name}")
        if source_name in self.media_states:
            self.media_states[source_name]['playing'] = True
    
    def _on_media_pause(self, event):
        """
        Callback pour l'événement de pause média
        """
        source_name = event.getSourceName()
        self.logger.info(f"Média en pause: {source_name}")
        if source_name in self.media_states:
            self.media_states[source_name]['playing'] = False
    
    def _on_media_stop(self, event):
        """
        Callback pour l'événement d'arrêt média
        """
        source_name = event.getSourceName()
        self.logger.info(f"Média arrêté: {source_name}")
        if source_name in self.media_states:
            self.media_states[source_name]['playing'] = False
            self.media_states[source_name]['position'] = 0
    
    def _on_media_end(self, event):
        """
        Callback pour l'événement de fin média
        """
        source_name = event.getSourceName()
        self.logger.info(f"Média terminé: {source_name}")
        if source_name in self.media_states:
            self.media_states[source_name]['playing'] = False
            self.media_states[source_name]['position'] = 0
