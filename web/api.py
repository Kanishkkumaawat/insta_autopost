
# --- Comment-to-DM Endpoints ---

@router.get("/comment-to-dm/status")
async def get_comment_to_dm_status(account_id: Optional[str] = None, app: InstaForgeApp = Depends(get_app)):
    """Get comment-to-DM status"""
    try:
        if not app.comment_to_dm_service:
            raise HTTPException(status_code=500, detail="Service not initialized")
            
        if not account_id:
            accounts = app.account_service.list_accounts()
            if not accounts:
                raise HTTPException(status_code=404, detail="No accounts configured")
            account_id = accounts[0].account_id
            
        status_info = app.comment_to_dm_service.get_status(account_id)
        return {"account_id": account_id, "status": status_info}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

@router.get("/comment-to-dm/config")
async def get_comment_to_dm_config(account_id: Optional[str] = None):
    """Get comment-to-DM config"""
    try:
        accounts = config_manager.load_accounts()
        if not account_id:
            if not accounts:
                raise HTTPException(status_code=404, detail="No accounts found")
            account = accounts[0]
            account_id = account.account_id
        else:
            account = next((a for a in accounts if a.account_id == account_id), None)
            if not account:
                raise HTTPException(status_code=404, detail="Account not found")
        
        return {
            "account_id": account_id,
            "config": account.comment_to_dm.dict() if account.comment_to_dm else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get config: {str(e)}")

@router.put("/comment-to-dm/config")
async def update_comment_to_dm_config(request: Request, account_id: Optional[str] = None, app: InstaForgeApp = Depends(get_app)):
    """Update comment-to-DM config"""
    try:
        body = await request.json()
        accounts = config_manager.load_accounts()
        
        if not account_id:
            if not accounts:
                raise HTTPException(status_code=404, detail="No accounts found")
            account_idx = 0
            account = accounts[0]
            account_id = account.account_id
        else:
            found = False
            for i, acc in enumerate(accounts):
                if acc.account_id == account_id:
                    account_idx = i
                    account = acc
                    found = True
                    break
            if not found:
                raise HTTPException(status_code=404, detail="Account not found")
        
        # Update config
        new_config_data = account.comment_to_dm.dict() if account.comment_to_dm else {}
        new_config_data.update({
            "enabled": body.get("enabled", False),
            "trigger_keyword": body.get("trigger_keyword", "AUTO"),
            "dm_message_template": body.get("dm_message_template", ""),
            "link_to_send": body.get("link_to_send", ""),
        })
        
        # Helper to filter out None values if needed, but dict() should handle defaults if we reconstruct
        # But we need to update the account object
        account_data = account.dict()
        account_data['comment_to_dm'] = new_config_data
        
        # Validate and replace
        updated_account = Account(**account_data)
        accounts[account_idx] = updated_account
        
        config_manager.save_accounts(accounts)
        
        # Reload app
        app.accounts = accounts
        app.account_service.update_accounts(accounts)
        
        return {"status": "success", "account_id": account_id, "config": updated_account.comment_to_dm.dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update config: {str(e)}")

@router.post("/comment-to-dm/post/{media_id}/file")
async def set_post_dm_file(request: Request, media_id: str, account_id: Optional[str] = None, app: InstaForgeApp = Depends(get_app)):
    """Set post specific DM file"""
    try:
        body = await request.json()
        file_path = body.get("file_path")
        file_url = body.get("file_url")
        trigger_mode = body.get("trigger_mode", "AUTO")
        trigger_word = body.get("trigger_word")
        
        if not file_url and not file_path:
             raise HTTPException(status_code=400, detail="File URL or path required")
             
        if not app.comment_to_dm_service:
            raise HTTPException(status_code=500, detail="Service not initialized")

        if not account_id:
            accounts = app.account_service.list_accounts()
            if not accounts:
                 raise HTTPException(status_code=404, detail="No accounts configured")
            account_id = accounts[0].account_id
            
        app.comment_to_dm_service.post_dm_config.set_post_dm_file(
            account_id=account_id,
            media_id=media_id,
            file_path=file_path,
            file_url=file_url,
            trigger_mode=trigger_mode,
            trigger_word=trigger_word,
        )
        
        return {
            "status": "success",
            "account_id": account_id,
            "media_id": media_id,
            "file_url": file_url or file_path,
            "trigger_mode": trigger_mode,
            "trigger_word": trigger_word,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set post DM: {str(e)}")

@router.get("/comment-to-dm/post/{media_id}/file")
async def get_post_dm_file(media_id: str, account_id: Optional[str] = None, app: InstaForgeApp = Depends(get_app)):
    """Get post specific DM config"""
    try:
        if not app.comment_to_dm_service:
            raise HTTPException(status_code=500, detail="Service not initialized")
            
        if not account_id:
            accounts = app.account_service.list_accounts()
            if not accounts:
                 raise HTTPException(status_code=404, detail="No accounts configured")
            account_id = accounts[0].account_id
            
        config = app.comment_to_dm_service.post_dm_config.get_post_dm_config(
            account_id=account_id,
            media_id=media_id,
        )
        
        if config:
            return {
                "account_id": account_id,
                "media_id": media_id,
                "file_url": config.get("file_url"),
                "trigger_mode": config.get("trigger_mode", "AUTO"),
                "trigger_word": config.get("trigger_word"),
                "has_config": True,
            }
        return {"account_id": account_id, "media_id": media_id, "has_config": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get post DM: {str(e)}")

@router.delete("/comment-to-dm/post/{media_id}/file")
async def remove_post_dm_file(media_id: str, account_id: Optional[str] = None, app: InstaForgeApp = Depends(get_app)):
    """Remove post specific DM config"""
    try:
        if not app.comment_to_dm_service:
            raise HTTPException(status_code=500, detail="Service not initialized")
            
        if not account_id:
            accounts = app.account_service.list_accounts()
            if not accounts:
                 raise HTTPException(status_code=404, detail="No accounts configured")
            account_id = accounts[0].account_id
            
        app.comment_to_dm_service.post_dm_config.remove_post_dm_file(
            account_id=account_id,
            media_id=media_id,
        )
        return {"status": "success", "account_id": account_id, "media_id": media_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove post DM: {str(e)}")
