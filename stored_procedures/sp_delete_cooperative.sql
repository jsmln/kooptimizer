-- Stored Procedure: Delete Cooperative
-- Description: Soft/hard delete cooperative and all related data across 5 tables

DROP FUNCTION IF EXISTS sp_delete_cooperative(INTEGER, BOOLEAN);

CREATE OR REPLACE FUNCTION sp_delete_cooperative(
    p_coop_id INTEGER,
    p_hard_delete BOOLEAN DEFAULT FALSE
)
RETURNS TABLE(
    success BOOLEAN,
    message TEXT
) AS $$
BEGIN
    -- Check if cooperative exists
    IF NOT EXISTS (SELECT 1 FROM cooperatives WHERE coop_id = p_coop_id) THEN
        RETURN QUERY SELECT FALSE, 'Cooperative not found';
        RETURN;
    END IF;
    
    IF p_hard_delete THEN
        -- Hard delete: Remove all related records
        -- Delete in order due to foreign key constraints
        
        -- Delete members
        DELETE FROM members WHERE coop_id = p_coop_id;
        
        -- Delete officers
        DELETE FROM officers WHERE coop_id = p_coop_id;
        
        -- Delete financial data
        DELETE FROM financial_data WHERE coop_id = p_coop_id;
        
        -- Delete profile data
        DELETE FROM profile_data WHERE coop_id = p_coop_id;
        
        -- Delete announcements recipients related to this cooperative
        DELETE FROM announcement_recipients WHERE coop_id = p_coop_id;
        
        -- Delete announcement officer recipients related to this cooperative's officers
        DELETE FROM announcement_officer_recipients 
        WHERE officer_id IN (SELECT officer_id FROM officers WHERE coop_id = p_coop_id);
        
        -- Finally delete the cooperative
        DELETE FROM cooperatives WHERE coop_id = p_coop_id;
        
        RETURN QUERY SELECT TRUE, 'Cooperative and all related data permanently deleted';
    ELSE
        -- Soft delete: Mark approval status as 'rejected' or add a deleted_at timestamp
        -- Note: This assumes you want to keep the data but mark it as inactive
        
        -- Update profile data status
        UPDATE profile_data SET
            approval_status = 'rejected',
            updated_at = NOW()
        WHERE coop_id = p_coop_id;
        
        -- Update financial data status
        UPDATE financial_data SET
            approval_status = 'rejected',
            updated_at = NOW()
        WHERE coop_id = p_coop_id;
        
        -- Update cooperative timestamp
        UPDATE cooperatives SET
            updated_at = NOW()
        WHERE cooperatives.coop_id = p_coop_id;
        
        RETURN QUERY SELECT TRUE, 'Cooperative marked as inactive (soft delete)';
    END IF;
    
EXCEPTION WHEN OTHERS THEN
    RETURN QUERY SELECT FALSE, SQLERRM;
END;
$$ LANGUAGE plpgsql;
