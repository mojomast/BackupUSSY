                    self.update_progress(100, f"Job failed: {final_error_msg[:50]}...") # Show truncated error on progress
                    self.log_message(f"Archive job finished with errors: {final_error_msg}")
                
            except Exception as e: # Outer catch-all for unexpected errors
                self.log_message(f"Unexpected error during archive job: {e}")
                self.logger.error(f"Unexpected archive job error: {e}", exc_info=True)
                job_result_for_event_loop['error'] = job_result_for_event_loop.get('error') or str(e) # Preserve earlier error if any
                job_result_for_event_loop['success'] = False
            
            finally:
                # Ensure JOB_DONE is always sent with the most current job_result state
                self.window.write_event_value('-JOB_DONE-', job_result_for_event_loop)
        
        def handle_second_copy(self, folder_path, device, compression, progress_callback):
            """Handle second tape copy for streaming mode."""
            result = sg.popup_yes_no(
                'Second Copy',
                'Insert second tape and click Yes to create second copy.',
                title='Second Tape Copy'
            )
            
            if result == 'Yes':
                self.log_message("Creating second copy...")
                self.tape_manager.rewind_tape(device)
                success = self.tape_manager.stream_to_tape(
                    folder_path, device, compression, progress_callback
                )
                if success:
                    self.log_message("Second copy completed successfully")
                else:
                    self.log_message("Second copy failed")
        
        def handle_second_copy_cached(self, archive_path, device, progress_callback):
            """Handle second tape copy for cached mode."""
            result = sg.popup_yes_no(
                'Second Copy',
                'Insert second tape and click Yes to create second copy.',
                title='Second Tape Copy'
            )
            
            if result == 'Yes':
                self.log_message("Writing second copy...")
                self.tape_manager.rewind_tape(device)
                success, bytes_written = self.tape_manager.write_archive_to_tape(
                    archive_path, device, progress_callback
                )
                if success:
                    self.log_message(f"Second copy completed successfully ({bytes_written} bytes)")
                else:
                    self.log_message("Second copy failed")
        
        finally:
            # Ensure tape device is released
            if hasattr(self, 'tape_manager') and self.tape_manager:
                self.tape_manager.release_tape_device()
            
            # job_result_for_event_loop is initialized within the try block of run_archive_job (around line 627)
            # and should be updated by the try/except logic within run_archive_job.
            # If it's somehow not defined here or not a dict, it indicates a flaw in the preceding logic.
            result_to_send = None
            if 'job_result_for_event_loop' in locals() and isinstance(job_result_for_event_loop, dict):
                result_to_send = job_result_for_event_loop
            else:
                self.logger.error("CRITICAL: job_result_for_event_loop not properly defined or not a dict in finally. Sending default error.")
                # config is available as it's an argument to run_archive_job
                result_to_send = {
                    'success': False, 
                    'error_message': 'Job result was not properly generated due to an internal error.',
                    'archive_id': config.get('archive_id'), # Use archive_id from config
                    'files_processed': 0,
                    'bytes_written': 0,
                    'mode': config.get('mode'),
                    'tape_name': config.get('tape_name')
                }

            self.window.write_event_value('-JOB_DONE-', result_to_send)
            self.current_job = None # Clear current job reference

    def run(self): # De-dented to be a method of LTOArchiveGUI
        """Main GUI event loop with tabbed interface support."""
        self.update_log(INIT_MESSAGE)
        self.populate_recovery_tapes()
        self.populate_search_tapes()
        self.update_tape_list()  # Populate management tape list on startup

        while True:
            event, values = self.window.read(timeout=100)

            if event == sg.WIN_CLOSED or event == '-EXIT-':
                if self.job_thread and self.job_thread.is_alive():
                    # Attempt to signal cancellation if a job is running
                    # This assumes a more robust cancellation mechanism might be added later
                    self.log_message("Attempting to cancel active job before exiting...", 'warn')
                    # self.handle_cancel_archive() # Or a generic cancel
                    # For now, just log and break. Proper cleanup might be needed.
                break

            # --- Archive Tab Events ---
            if event == '-START-':
                try:
                    config = {
                        'folder_path': values['-FOLDER-'],
                        'device': values['-DEVICE-'],
                        'mode': ArchiveMode.STREAM if values['-STREAM-'] else ArchiveMode.CACHED,
                        'compression': values['-COMPRESS-'],
                        'copies': 2 if values['-COPY2-'] else 1,
                        'archive_name': values['-ARCHIVE_NAME-'] or None,
                        'index_files': values['-INDEX_FILES-'],
                        'estimated_size': 0,
                        'file_count': 0
                    }
                    self.start_archive_job(config)
                except Exception as e:
                    self.log_message(f"Error starting archive: {e}", 'error')
                    sg.popup_error(f"Error starting archive: {e}")
                
            elif event == '-CALC_SIZE-':
                if values['-FOLDER-']:
                    self.update_folder_size(values['-FOLDER-'])
                else:
                    sg.popup('Please select a folder first to calculate its size.')

            elif event == '-REFRESH-': # Refresh tape devices
                devices = self.tape_manager.detect_tape_devices()
                if not devices:
                    devices = ['\\.\Tape0'] # Default
                self.window['-DEVICE-'].update(values=devices, value=devices[0] if devices else '')
                self.update_tape_status()

            elif event == '-PREVIEW-':
                self.handle_preview_files(values['-FOLDER-'])
            
            elif event == '-CANCEL-': # Placeholder for archive cancel
                # This needs to be connected to the job thread cancellation logic
                self.log_message("Cancel button clicked - cancellation logic to be implemented.", 'warn')
                if self.current_job:
                     # self.current_job.cancel() # Hypothetical cancel method on job object
                     self.window['-CANCEL-'].update(disabled=True)
                     self.window['-START-'].update(disabled=False)
                     self.log_message("Archive job cancellation requested.")
                else:
                    self.log_message("No active job to cancel.")

            # --- Recovery Tab Events ---
            elif event == '-RECOVERY_TAPE-':
                self.handle_recovery_tape_selection(values.get('-RECOVERY_TAPE-'))
            elif event == '-LOAD_TAPE-':
                self.handle_load_tape_contents(values.get('-RECOVERY_TAPE-'))
            elif event == '-RECOVERY_ARCHIVE-':
                self.handle_recovery_archive_selection(values.get('-RECOVERY_ARCHIVE-'))
            elif event == '-START_RECOVERY-':
                self.handle_start_recovery(values)
            elif event == '-CANCEL_RECOVERY-':
                self.handle_cancel_recovery()

            # --- Search Tab Events ---
            elif event == '-SEARCH_BTN-':
                self.handle_search(values)
            elif event == '-SEARCH_RESULTS-': # Table selection
                self.handle_search_selection(values.get('-SEARCH_RESULTS-'))
            elif event == '-SEARCH_RECOVER-':
                self.handle_search_recover(values)
            elif event == '-SEARCH_SHOW_ARCHIVE-':
                self.handle_search_show_archive(values)
            elif event == '-SEARCH_EXPORT-':
                self.handle_search_export()
            elif event == '-SEARCH_CLEAR-':
                self.handle_search_clear()
            elif event == '-ADVANCED_SEARCH-':
                self.handle_advanced_search()

            # --- Management Tab Events ---
            elif event == '-TAPE_LIST-': # Table selection
                self.handle_tape_selection(values.get('-TAPE_LIST-'))
            elif event == '-ADD_TAPE-':
                self.handle_add_tape()
            elif event == '-EDIT_TAPE-':
                self.handle_edit_tape(values)
            elif event == '-DELETE_TAPE-':
                self.handle_delete_tape(values)
            elif event == '-BROWSE_TAPE-': # Different from BROWSE_ARCHIVES
                self.handle_browse_tape(values)
            elif event == '-EXPORT_INVENTORY-':
                self.handle_export_inventory()
            elif event == '-IMPORT_DATA-':
                self.handle_import_data()
            elif event == '-DB_MAINTENANCE-':
                self.handle_db_maintenance()
            elif event == '-BROWSE_ARCHIVES-': # General archive browser
                self.handle_browse_archives()

            # --- JOB DONE Event --- (From run_archive_job thread)
            elif event == '-JOB_DONE-':
                job_result = values[event]
                if job_result:
                    status = job_result.get('status', 'unknown')
                    archive_name_msg = f" for archive '{job_result.get('archive_name', 'N/A')}'" if job_result.get('archive_name') else ""
                    self.log_message(f"Archive job finished with status: {status}{archive_name_msg}")
                    
                    if job_result.get('error_message'):
                        self.log_message(f"Error: {job_result['error_message']}", 'error')
                        sg.popup_error(f"Job Failed: {job_result['error_message']}")
                    elif status == 'completed' or status == 'indexed':
                        self.log_message(f"Successfully processed {job_result.get('files_processed', 0)} files, {job_result.get('bytes_written', 0)} bytes written.")
                    elif status == 'streaming_failed' or status == 'caching_failed':
                         self.log_message(f"Job failed. See logs for details.", 'error')
                    else:
                        self.log_message("Job completed.") # Generic completion

                    # Re-enable UI elements
                    self.window['-START-'].update(disabled=False)
                    self.window['-CANCEL-'].update(disabled=True)
                    self.window['-FOLDER-'].update(disabled=False)
                    self.window['-DEVICE-'].update(disabled=False)
                    # Add other elements like radio buttons, checkboxes if they were disabled
                    
                    # Refresh lists and stats based on job outcome
                    if status not in ['streaming_failed', 'caching_failed']:
                        self.update_tape_list() # This also updates management stats
                        self.populate_recovery_tapes()
                        self.populate_search_tapes()
                        self.update_tape_status() # Update current tape status
                else:
                    self.log_message("Job finished, but no result data was received.", 'warn')
                    
                # Clear progress and reset job tracking
                self.update_progress(0, "Ready")
                self.current_job = None
                self.job_thread = None # Clear the thread reference
            
        self.window.close()
    
def handle_preview_files(self, folder_path):
        """Handle preview files button click."""
        if not folder_path:
            sg.popup_error('Error', 'Please select a source folder')
            return
        
        try:
            files = self.archive_manager.get_file_list(folder_path)
            preview_text = f"Files to be archived ({len(files)} total):\n\n"
            for file_path in files[:100]:  # Show first 100 files
                preview_text += f"{file_path}\n"
            
            if len(files) > 100:
                preview_text += f"\n... and {len(files) - 100} more files"
            
            sg.popup_scrolled(preview_text, title='File Preview', size=(80, 30))
        except Exception as e:
            sg.popup_error('Preview Error', f'Failed to preview files: {e}')
    
def handle_recovery_tape_selection(self, tape_selection):
        """Handle recovery tape selection."""
        if not tape_selection:
            return
        
        try:
            tape_label = tape_selection.split(' (')[0]
            tape = self.db_manager.find_tape_by_label(tape_label)
            if tape:
                archives = self.db_manager.get_tape_contents(tape['tape_id'])
                archive_options = [archive['archive_name'] for archive in archives]
                self.window['-RECOVERY_ARCHIVE-'].update(values=archive_options)
        except Exception as e:
            self.logger.error(f"Failed to load tape archives: {e}")
    
def handle_search(self, values):
        """Handle search button click."""
        query = values['-SEARCH_QUERY-'].strip()
        if not query:
            sg.popup('Please enter a search query')
            return
        
        try:
            filters = {
                'file_type': values['-SEARCH_TYPE-'] if values['-SEARCH_TYPE-'] != 'All Types' else None,
                'tape_label': values['-SEARCH_TAPE-'] if values['-SEARCH_TAPE-'] != 'All Tapes' else None
            }
            
            results = self.search_interface.search_files(query, filters)
            self.search_interface.display_search_results(results)
            
            # Update count
            self.window['-SEARCH_COUNT-'].update(f'{len(results)} files found')
            
        except Exception as e:
            sg.popup_error('Search Error', f'Search failed: {e}')
    
def handle_advanced_search(self):
        """Handle advanced search button click."""
        try:
            adv_gui = AdvancedSearchGUI(self.db_manager, self.advanced_search)
            adv_gui.run_advanced_search_interface()
        except Exception as e:
            sg.popup_error('Advanced Search Error', f'Failed to open advanced search: {e}')
    
def handle_browse_archives(self):
        """Handle browse archives button click."""
        try:
            self.tape_browser.run_browser_interface()
        except Exception as e:
            sg.popup_error('Browser Error', f'Failed to open tape browser: {e}')
    
    def update_tape_list(self):
        """Update the tape list in all tabs after successful archiving operations."""
        try:
            tapes = self.db_manager.get_all_tapes()
            
            # Update main tape selection combo
            tape_labels = [f"{tape['tape_label']} ({tape['tape_device']})" for tape in tapes]
            if self.window and '-DEVICE-' in self.window.AllKeysDict:
                current_value = self.window['-DEVICE-'].get()
                self.window['-DEVICE-'].update(values=tape_labels)
                # Try to maintain current selection if it still exists
                if current_value in tape_labels:
                    self.window['-DEVICE-'].update(value=current_value)
                elif tape_labels:
                    self.window['-DEVICE-'].update(value=tape_labels[0])
            
            # Update statistics
            self.update_statistics()
            
            logger.info(f"Updated tape list with {len(tapes)} tapes")
            
        except Exception as e:
            logger.error(f"Failed to update tape list: {e}", exc_info=True)
    
    def populate_recovery_tapes(self):
        """Populate tape list in recovery tab."""
        try:
            if not self.window:
                return
                
            tapes = self.db_manager.get_all_tapes()
            tape_options = [f"{tape['tape_label']} - {tape.get('archive_count', 0)} archives" for tape in tapes]
            
            if '-RECOVERY_TAPE-' in self.window.AllKeysDict:
                self.window['-RECOVERY_TAPE-'].update(values=tape_options)
                if tape_options:
                    self.window['-RECOVERY_TAPE-'].update(value=tape_options[0])
            
            logger.info(f"Populated recovery tapes with {len(tapes)} options")
            
        except Exception as e:
            logger.error(f"Failed to populate recovery tapes: {e}", exc_info=True)
    
    def populate_search_tapes(self):
        """Populate tape list in search tab."""
        try:
            if not self.window:
                return
                
            tapes = self.db_manager.get_all_tapes()
            tape_options = ['All Tapes'] + [f"{tape['tape_label']}" for tape in tapes]
            
            if '-SEARCH_TAPE-' in self.window.AllKeysDict:
                self.window['-SEARCH_TAPE-'].update(values=tape_options)
                self.window['-SEARCH_TAPE-'].update(value='All Tapes')
            
            logger.info(f"Populated search tapes with {len(tapes)} options")
            
        except Exception as e:
            logger.error(f"Failed to populate search tapes: {e}", exc_info=True)
    
    def update_statistics(self):
        """Update the statistics display."""
        try:
            if not self.window or '-STATS-' not in self.window.AllKeysDict:
                return
                
            stats = self.db_manager.get_database_stats()
            total_data_gb = (stats.get('total_data_bytes', 0) / (1024**3))
            
            stats_text = f"""Tapes: {stats['total_tapes']}
Archives: {stats['total_archives']}
Files: {stats['total_files']}
Data: {total_data_gb:.1f} GB
Active: {stats.get('active_tapes', 0)}"""
            
            self.window['-STATS-'].update(stats_text)
            logger.info(f"Updated statistics: {stats['total_tapes']} tapes, {stats['total_archives']} archives, {stats['total_files']} files")
            
        except Exception as e:
            logger.error(f"Failed to update statistics: {e}", exc_info=True)
        """Update the tape list in management tab."""
        try:
            tapes = self.db_manager.get_all_tapes()
            table_data = []
            
            for tape in tapes:
                archives = self.db_manager.get_tape_contents(tape['tape_id'])
                size_gb = (tape.get('total_size_bytes', 0) or 0) / (1024**3)
                
                table_data.append([
                    tape['tape_label'],
                    tape.get('tape_device', 'Unknown'),
                    tape.get('tape_status', 'unknown'),
                    f"{size_gb:.1f} GB",
                    str(len(archives)),
                    tape.get('created_date', 'Unknown')[:10] if tape.get('created_date') else 'Unknown'
                ])
            
            self.window['-TAPE_LIST-'].update(values=table_data)
            self.update_management_stats()
            
        except Exception as e:
            self.logger.error(f"Failed to update tape list: {e}")
    
def handle_add_tape(self):
        """Handle add tape button click."""
        layout = [
            [sg.Text('Add New Tape to Library')],
            [sg.Text('Tape Label:', size=(12, 1)), sg.Input(key='-NEW_TAPE_LABEL-', size=(20, 1))],
            [sg.Text('Device:', size=(12, 1)), sg.Input(key='-NEW_TAPE_DEVICE-', size=(20, 1))],
            [sg.Text('Notes:', size=(12, 1))],
            [sg.Multiline(key='-NEW_TAPE_NOTES-', size=(40, 3))],
            [sg.Button('Add Tape', key='-ADD_NEW_TAPE-'), sg.Button('Cancel', key='-CANCEL_ADD-')]
        ]
        
        add_window = sg.Window('Add Tape', layout, modal=True)
        
        while True:
            event, values = add_window.read()
            
            if event in (sg.WIN_CLOSED, '-CANCEL_ADD-'):
                break
            elif event == '-ADD_NEW_TAPE-':
                try:
                    tape_id = self.db_manager.add_tape(
                        tape_label=values['-NEW_TAPE_LABEL-'],
                        device=values['-NEW_TAPE_DEVICE-'],
                        notes=values['-NEW_TAPE_NOTES-']
                    )
                    sg.popup(f'Tape added successfully with ID: {tape_id}')
                    self.update_tape_list()
                    self.populate_recovery_tapes()
                    self.populate_search_tapes()
                    break
                except Exception as e:
                    sg.popup_error('Add Tape Error', f'Failed to add tape: {e}')
        
        add_window.close()
    
def handle_db_maintenance(self):
        """Handle database maintenance button click."""
        try:
            from database_init import DatabaseInitializer
            
            db_init = DatabaseInitializer()
            
            layout = [
                [sg.Text('Database Maintenance', font=('Arial', 12, 'bold'))],
                [sg.HSeparator()],
                [sg.Button('Check Integrity', key='-CHECK_INTEGRITY-'),
                 sg.Button('Optimize Database', key='-OPTIMIZE_DB-')],
                [sg.Button('Backup Database', key='-BACKUP_DB-'),
                 sg.Button('Cleanup Temp Files', key='-CLEANUP_DB-')],
                [sg.HSeparator()],
                [sg.Multiline(size=(60, 10), key='-MAINTENANCE_LOG-', disabled=True)],
                [sg.Button('Close', key='-CLOSE_MAINTENANCE-')]
            ]
            
            maint_window = sg.Window('Database Maintenance', layout, modal=True)
            
            while True:
                event, values = maint_window.read()
                
                if event in (sg.WIN_CLOSED, '-CLOSE_MAINTENANCE-'):
                    break
                elif event == '-CHECK_INTEGRITY-':
                    result = db_init.check_database_integrity()
                    maint_window['-MAINTENANCE_LOG-'].print(f"Integrity check: {result}\n")
                elif event == '-OPTIMIZE_DB-':
                    db_init.optimize_database()
                    maint_window['-MAINTENANCE_LOG-'].print("Database optimized\n")
                elif event == '-BACKUP_DB-':
                    backup_path = db_init.backup_database()
                    maint_window['-MAINTENANCE_LOG-'].print(f"Database backed up to: {backup_path}\n")
                elif event == '-CLEANUP_DB-':
                    db_init.cleanup_temp_files()
                    maint_window['-MAINTENANCE_LOG-'].print("Temporary files cleaned up\n")
            
            maint_window.close()
            
    except Exception as e:
        sg.popup_error('Maintenance Error', f'Database maintenance failed: {e}')

    def handle_load_tape_contents(self, tape_selection):
        """Handle load tape contents button click."""
        if not tape_selection:
            sg.popup('Please select a tape first')
            return
        
        try:
            tape_label = tape_selection.split(' (')[0]
            tape = self.db_manager.find_tape_by_label(tape_label)
            if tape:
                archives = self.db_manager.get_tape_contents(tape['tape_id'])
                archive_options = [archive['archive_name'] for archive in archives]
                self.window['-RECOVERY_ARCHIVE-'].update(values=archive_options)
                self.window['-START_RECOVERY-'].update(disabled=False)
                self.update_log(f"Loaded {len(archives)} archives from tape {tape_label}", 'recovery')
        except Exception as e:
            sg.popup_error('Load Error', f'Failed to load tape contents: {e}')

    def handle_recovery_archive_selection(self, archive_selection):
        """Handle recovery archive selection."""
        if not archive_selection:
            return
        
        try:
            archive = self.db_manager.find_archive_by_name(archive_selection)
            if archive:
                files = self.db_manager.get_archive_files(archive['archive_id'])
                
                # Format files for table display
                table_data = []
                for file_info in files:
                    size_mb = (file_info.get('file_size_bytes', 0) or 0) / (1024*1024)
                    table_data.append([
                        file_info['file_path'],
                        f"{size_mb:.2f} MB",
                        file_info.get('file_modified', 'Unknown')[:16] if file_info.get('file_modified') else 'Unknown',
                        file_info.get('file_type', 'Unknown')
                    ])
                
                self.window['-RECOVERY_FILES-'].update(values=table_data)
                self.update_log(f"Loaded {len(files)} files from archive {archive_selection}", 'recovery')
        except Exception as e:
            sg.popup_error('Archive Error', f'Failed to load archive files: {e}')

    def handle_start_recovery(self, values):
        """Handle start recovery button click."""
        tape_selection = values['-RECOVERY_TAPE-']
        archive_selection = values['-RECOVERY_ARCHIVE-']
        output_dir = values['-RECOVERY_OUTPUT-']
        
        if not all([tape_selection, archive_selection, output_dir]):
            sg.popup_error('Recovery Error', 'Please select tape, archive, and output directory')
            return
        
        try:
            # Disable controls
            self.window['-START_RECOVERY-'].update(disabled=True)
            self.window['-CANCEL_RECOVERY-'].update(disabled=False)
            
            # Get recovery mode
            recover_all = values['-RECOVER_ALL-']
            selected_files = None
            
            if not recover_all:
                # Get selected files from table
                selected_rows = values['-RECOVERY_FILES-']
                if not selected_rows:
                    sg.popup('Please select files to recover or choose "Complete Archive" mode')
                    self.window['-START_RECOVERY-'].update(disabled=False)
                    self.window['-CANCEL_RECOVERY-'].update(disabled=True)
                    return
                
                # Extract file paths from selected rows
                table_data = self.window['-RECOVERY_FILES-'].get()
                selected_files = [table_data[row][0] for row in selected_rows]
            
            # Start recovery in separate thread
            def recovery_job():
                try:
                    tape_label = tape_selection.split(' (')[0]
                    tape = self.db_manager.find_tape_by_label(tape_label)
                    
                    def progress_callback(data):
                        if isinstance(data, dict):
                            if 'percent' in data:
                                self.window['-RECOVERY_PROGRESS-'].update(data['percent'])
                                self.window['-RECOVERY_STATUS-'].update(data.get('status', ''))
                            else:
                                self.update_log(data.get('status', str(data)), 'recovery')
                        else:
                            self.update_log(str(data), 'recovery')
                    
                    if recover_all:
                        result = self.recovery_manager.extract_archive(
                            tape['tape_device'], archive_selection, output_dir, progress_callback
                        )
                    else:
                        result = self.recovery_manager.extract_specific_files(
                            tape['tape_device'], archive_selection, selected_files, output_dir, progress_callback
                        )
                    
                    if result:
                        self.update_log("Recovery completed successfully", 'recovery')
                        
                        # Verify if requested
                        if values['-VERIFY_RECOVERY-']:
                            self.update_log("Verifying recovered files...", 'recovery')
                            archive = self.db_manager.find_archive_by_name(archive_selection)
                            verification_result = self.recovery_manager.verify_recovered_files(
                                output_dir, archive['archive_id']
                            )
                            if verification_result:
                                self.update_log("File verification passed", 'recovery')
                            else:
                                self.update_log("File verification failed - some files may be corrupted", 'recovery')
                    else:
                        self.update_log("Recovery failed", 'recovery')
                    
                except Exception as e:
                    self.update_log(f"Recovery error: {e}", 'recovery')
                
                finally:
                    # Re-enable controls
                    self.window.write_event_value('-RECOVERY_DONE-', None)
            
            threading.Thread(target=recovery_job, daemon=True).start()
            
        except Exception as e:
            sg.popup_error('Recovery Error', f'Failed to start recovery: {e}')
            self.window['-START_RECOVERY-'].update(disabled=False)
            self.window['-CANCEL_RECOVERY-'].update(disabled=True)

    def handle_cancel_recovery(self):
        """Handle cancel recovery button click."""
        self.update_log("Recovery cancellation requested", 'recovery')
        # TODO: Implement proper cancellation mechanism

    def handle_search_selection(self, selection):
        """Handle search results selection."""
        try:
            if selection:
                table_data = self.window['-SEARCH_RESULTS-'].get()
                if selection and len(table_data) > selection[0]:
                    selected_file = table_data[selection[0]]
                    
                    # Get file details
                    file_path = selected_file[0]
                    archive_name = selected_file[3]
                    tape_label = selected_file[4]
                    
                    details = f"File: {file_path}\n"
                    details += f"Size: {selected_file[1]}\n"
                    details += f"Modified: {selected_file[2]}\n"
                    details += f"Archive: {archive_name}\n"
                    details += f"Tape: {tape_label}\n"
                    
                    self.window['-SEARCH_DETAILS-'].update(details)
                    self.window['-SEARCH_RECOVER-'].update(disabled=False)
                    self.window['-SEARCH_SHOW_ARCHIVE-'].update(disabled=False)
        except Exception as e:
            self.logger.error(f"Tape selection error: {e}")

def handle_search_recover(self, values):
    """Handle recover selected files from search."""
    try:
        selected_rows = values['-SEARCH_RESULTS-']
        if not selected_rows:
            sg.popup('Please select files to recover')
    {{ ... }}
        else:
            sg.popup_error(f'Failed to recover: {file_path}')
    except Exception as e:
        sg.popup_error('Recovery Error', f'Search recovery failed: {e}')

def handle_search_show_archive(self, values):
    """Handle show selected file in archive browser."""
    try:
        selected_rows = values['-SEARCH_RESULTS-']
        if not selected_rows:
            sg.popup('Please select a file first')
    {{ ... }}
    # Open tape browser and navigate to archive
    self.tape_browser.run_browser_interface(archive_name)
    except Exception as e:
        sg.popup_error('Browser Error', f'Failed to show archive: {e}')

def handle_search_export(self):
    """Handle export search results."""
    try:
        table_data = self.window['-SEARCH_RESULTS-'].get()
        if not table_data:
            sg.popup('No search results to export')
    {{ ... }}
    self.search_interface.export_search_results(table_data, export_path)
    sg.popup(f'Search results exported to: {export_path}')
    except Exception as e:
        sg.popup_error('Export Error', f'Failed to export results: {e}')

def handle_search_clear(self):
    """Handle clear search results."""
    self.window['-SEARCH_RESULTS-'].update(values=[])
    self.window['-SEARCH_DETAILS-'].update('')
    self.window['-SEARCH_COUNT-'].update('0 files found')
    self.window['-SEARCH_RECOVER-'].update(disabled=True)
    self.window['-SEARCH_SHOW_ARCHIVE-'].update(disabled=True)

def handle_tape_selection(self, selection):
    """Handle tape selection in management tab."""
    try:
        if selection:
            table_data = self.window['-TAPE_LIST-'].get()
            if selection and len(table_data) > selection[0]:
    {{ ... }}
    # Enable management buttons
    self.window['-EDIT_TAPE-'].update(disabled=False)
    self.window['-DELETE_TAPE-'].update(disabled=False)
    self.window['-BROWSE_TAPE-'].update(disabled=False)
    except Exception as e:
        self.logger.error(f"Search selection error: {e}")

def handle_edit_tape(self, values):
    """Handle edit tape button click."""
    try:
        selected_rows = values['-TAPE_LIST-']
        if not selected_rows:
            sg.popup('Please select a tape to edit')
            return
        
        table_data = self.window['-TAPE_LIST-'].get()
        tape_label = table_data[selected_rows[0]][0]
        tape = self.db_manager.find_tape_by_label(tape_label)
        
        if tape:
            # Update tape in database
            new_label = values['-TAPE_DETAIL_LABEL-']
            new_status = values['-TAPE_DETAIL_STATUS-']
            new_notes = values['-TAPE_DETAIL_NOTES-']
            
            self.db_manager.update_tape(
                tape['tape_id'],
                tape_label=new_label,
                tape_status=new_status,
                notes=new_notes
            )
            
            sg.popup('Tape updated successfully')
            self.update_tape_list()
            self.populate_recovery_tapes()
            self.populate_search_tapes()
    except Exception as e:
        sg.popup_error('Edit Error', f'Failed to edit tape: {e}')

def handle_delete_tape(self, values):
    """Handle delete tape button click."""
    try:
        selected_rows = values['-TAPE_LIST-']
        if not selected_rows:
            sg.popup('Please select a tape to delete')
            return
        
        table_data = self.window['-TAPE_LIST-'].get()
        tape_label = table_data[selected_rows[0]][0]
        
        # Confirm deletion
        result = sg.popup_yes_no(
            f'Are you sure you want to delete tape "{tape_label}"?\n'
            'This will remove all associated archive and file records.',
            title='Confirm Deletion'
        )
        
        if result == 'Yes':
            tape = self.db_manager.find_tape_by_label(tape_label)
            if tape:
                self.db_manager.delete_tape(tape['tape_id'])
                sg.popup('Tape deleted successfully')
                self.update_tape_list()
                self.populate_recovery_tapes()
                self.populate_search_tapes()
                
                # Clear details
                self.window['-TAPE_DETAIL_LABEL-'].update('', disabled=True)
                self.window['-TAPE_DETAIL_STATUS-'].update('', disabled=True)
                self.window['-TAPE_DETAIL_NOTES-'].update('', disabled=True)
                
                # Disable buttons
                self.window['-EDIT_TAPE-'].update(disabled=True)
                self.window['-DELETE_TAPE-'].update(disabled=True)
                self.window['-BROWSE_TAPE-'].update(disabled=True)
    except Exception as e:
        sg.popup_error('Delete Error', f'Failed to delete tape: {e}')

def handle_browse_tape(self, values):
    """Handle browse tape button click."""
    try:
        selected_rows = values['-TAPE_LIST-']
        if not selected_rows:
            sg.popup('Please select a tape to browse')
            return
        
        table_data = self.window['-TAPE_LIST-'].get()
        tape_label = table_data[selected_rows[0]][0]
        
        # Open tape browser for specific tape
        self.tape_browser.run_browser_interface(tape_filter=tape_label)
    except Exception as e:
        sg.popup_error('Browse Error', f'Failed to browse tape: {e}')

def handle_export_inventory(self):
    """Handle export inventory button click."""
    try:
        export_path = sg.popup_get_file(
            'Export Tape Inventory',
            save_as=True,
            file_types=[('CSV Files', '*.csv'), ('JSON Files', '*.json')],
            default_extension='.csv'
        )
        
        if export_path:
            if export_path.lower().endswith('.json'):
                self.db_manager.export_inventory_json(export_path)
            else:
                self.db_manager.export_inventory_csv(export_path)
            
            sg.popup(f'Inventory exported to: {export_path}')
    except Exception as e:
        sg.popup_error('Export Error', f'Failed to export inventory: {e}')

def handle_import_data(self):
    """Handle import data button click."""
    try:
        import_path = sg.popup_get_file(
            'Import Data',
            file_types=[('CSV Files', '*.csv'), ('JSON Files', '*.json')]
        )
        
        if import_path:
            result = sg.popup_yes_no(
                f'Import data from {import_path}?\n'
                'This may overwrite existing data.',
                title='Confirm Import'
            )
            
            if result == 'Yes':
                if import_path.lower().endswith('.json'):
                    records_imported = self.db_manager.import_inventory_json(import_path)
                else:
                    records_imported = self.db_manager.import_inventory_csv(import_path)
                
                sg.popup(f'Successfully imported {records_imported} records')
                self.update_tape_list()
                self.populate_recovery_tapes()
                self.populate_search_tapes()
    except Exception as e:
        sg.popup_error('Import Error', f'Failed to import data: {e}')



def main():
    """Main entry point."""
    try:
        app = LTOArchiveGUI()
        app.run()
    except Exception as e:
        sg.popup_error('Fatal Error', f'Application failed to start: {e}')
        logging.error(f"Fatal error: {e}")


if __name__ == '__main__':
    main()

