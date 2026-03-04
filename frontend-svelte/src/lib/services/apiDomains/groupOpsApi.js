import { API_URL, authHeaders, parseError } from '../apiCore.js';

export function createGroupOpsApi({ cacheGet, cacheSet, cacheInvalidate }) {
    return {
        async listGroups() {
            const cached = cacheGet('groups:list');
            if (cached) return cached;
            const response = await fetch(`${API_URL}/groups/`, {
                headers: authHeaders(),
            });
            if (!response.ok) throw new Error(await parseError(response));
            const data = await response.json();
            cacheSet('groups:list', data, 30000); // 30s TTL
            return data;
        },

        async createGroup(name, description = '') {
            const response = await fetch(`${API_URL}/groups/`, {
                method: 'POST',
                headers: authHeaders({ 'Content-Type': 'application/json' }),
                body: JSON.stringify({ name, description }),
            });
            if (!response.ok) throw new Error(await parseError(response));
            cacheInvalidate('groups:');
            return await response.json();
        },

        async getGroup(groupId) {
            const cached = cacheGet(`groups:${groupId}`);
            if (cached) return cached;
            const response = await fetch(`${API_URL}/groups/${groupId}`, {
                headers: authHeaders(),
            });
            if (!response.ok) throw new Error(await parseError(response));
            const data = await response.json();
            cacheSet(`groups:${groupId}`, data, 30000); // 30s TTL
            return data;
        },

        async updateGroup(groupId, data) {
            const response = await fetch(`${API_URL}/groups/${groupId}`, {
                method: 'PUT',
                headers: authHeaders({ 'Content-Type': 'application/json' }),
                body: JSON.stringify(data),
            });
            if (!response.ok) throw new Error(await parseError(response));
            return await response.json();
        },

        async deleteGroup(groupId) {
            const response = await fetch(`${API_URL}/groups/${groupId}`, {
                method: 'DELETE',
                headers: authHeaders(),
            });
            if (!response.ok) throw new Error(await parseError(response));
            cacheInvalidate('groups:');
            return await response.json();
        },

        async addGroupMembers(groupId, members) {
            const response = await fetch(`${API_URL}/groups/${groupId}/members`, {
                method: 'POST',
                headers: authHeaders({ 'Content-Type': 'application/json' }),
                body: JSON.stringify({ members }),
            });
            if (!response.ok) throw new Error(await parseError(response));
            cacheInvalidate('groups:');
            return await response.json();
        },

        async updateGroupMember(groupId, memberId, data) {
            const response = await fetch(`${API_URL}/groups/${groupId}/members/${memberId}`, {
                method: 'PUT',
                headers: authHeaders({ 'Content-Type': 'application/json' }),
                body: JSON.stringify(data),
            });
            if (!response.ok) throw new Error(await parseError(response));
            return await response.json();
        },

        async deleteGroupMember(groupId, memberId) {
            const response = await fetch(`${API_URL}/groups/${groupId}/members/${memberId}`, {
                method: 'DELETE',
                headers: authHeaders(),
            });
            if (!response.ok) throw new Error(await parseError(response));
            cacheInvalidate('groups:');
            return await response.json();
        },

        async getInventoryForecast(groupId) {
            const response = await fetch(`${API_URL}/inventory/forecast/${groupId}`, {
                headers: authHeaders(),
            });
            if (!response.ok) throw new Error(await parseError(response));
            return await response.json();
        },

        async getFulfillmentStatus(groupId) {
            const response = await fetch(`${API_URL}/inventory/fulfillment/${groupId}`, {
                headers: authHeaders(),
            });
            if (!response.ok) throw new Error(await parseError(response));
            return await response.json();
        },

        async markMembersReceived(groupId, memberIds) {
            const response = await fetch(`${API_URL}/inventory/fulfillment/${groupId}/mark-received`, {
                method: 'POST',
                headers: authHeaders({ 'Content-Type': 'application/json' }),
                body: JSON.stringify({ member_ids: memberIds, items_received: ['koper', 'baju'] }),
            });
            if (!response.ok) throw new Error(await parseError(response));
            return await response.json();
        },

        async updateMemberOperational(memberId, bajuSize, familyId) {
            const response = await fetch(`${API_URL}/inventory/members/${memberId}/operational`, {
                method: 'PUT',
                headers: authHeaders({ 'Content-Type': 'application/json' }),
                body: JSON.stringify({ baju_size: bajuSize, family_id: familyId }),
            });
            if (!response.ok) throw new Error(await parseError(response));
            return await response.json();
        },

        async getRoomingSummary(groupId) {
            const response = await fetch(`${API_URL}/rooming/summary/${groupId}`, {
                headers: authHeaders(),
            });
            if (!response.ok) throw new Error(await parseError(response));
            return await response.json();
        },

        async getGroupRooms(groupId) {
            const response = await fetch(`${API_URL}/rooming/group/${groupId}`, {
                headers: authHeaders(),
            });
            if (!response.ok) throw new Error(await parseError(response));
            return await response.json();
        },

        async createRoom(groupId, roomNumber, genderType = 'male', roomType = 'quad', capacity = 4) {
            const response = await fetch(`${API_URL}/rooming/group/${groupId}`, {
                method: 'POST',
                headers: authHeaders({ 'Content-Type': 'application/json' }),
                body: JSON.stringify({ room_number: roomNumber, gender_type: genderType, room_type: roomType, capacity }),
            });
            if (!response.ok) throw new Error(await parseError(response));
            return await response.json();
        },

        async deleteRoom(roomId) {
            const response = await fetch(`${API_URL}/rooming/${roomId}`, {
                method: 'DELETE',
                headers: authHeaders(),
            });
            if (!response.ok) throw new Error(await parseError(response));
            return await response.json();
        },

        async autoRooming(groupId, roomCapacity = 4) {
            const response = await fetch(`${API_URL}/rooming/auto/${groupId}`, {
                method: 'POST',
                headers: authHeaders({ 'Content-Type': 'application/json' }),
                body: JSON.stringify({ room_capacity: roomCapacity }),
            });
            if (!response.ok) throw new Error(await parseError(response));
            return await response.json();
        },

        async clearAutoRooming(groupId) {
            const response = await fetch(`${API_URL}/rooming/auto/${groupId}`, {
                method: 'DELETE',
                headers: authHeaders(),
            });
            if (!response.ok) throw new Error(await parseError(response));
            return await response.json();
        },

        async assignMemberToRoom(memberId, roomId) {
            const response = await fetch(`${API_URL}/rooming/assign`, {
                method: 'POST',
                headers: authHeaders({ 'Content-Type': 'application/json' }),
                body: JSON.stringify({ member_id: memberId, room_id: roomId }),
            });
            if (!response.ok) throw new Error(await parseError(response));
            return await response.json();
        },

        async unassignMember(memberId) {
            const response = await fetch(`${API_URL}/rooming/unassign/${memberId}`, {
                method: 'POST',
                headers: authHeaders(),
            });
            if (!response.ok) throw new Error(await parseError(response));
            return await response.json();
        },

        async shareGroup(groupId, pin, expiresInDays = 30) {
            const response = await fetch(`${API_URL}/groups/${groupId}/share`, {
                method: 'POST',
                headers: authHeaders({ 'Content-Type': 'application/json' }),
                body: JSON.stringify({ pin, expires_in_days: expiresInDays }),
            });
            if (!response.ok) throw new Error(await parseError(response));
            return await response.json();
        },

        async revokeShare(groupId) {
            const response = await fetch(`${API_URL}/groups/${groupId}/share`, {
                method: 'DELETE',
                headers: authHeaders(),
            });
            if (!response.ok) throw new Error(await parseError(response));
            return await response.json();
        },

        async getSharedManifest(sharedToken, pin) {
            const response = await fetch(`${API_URL}/shared/manifest/${sharedToken}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pin }),
            });
            if (!response.ok) throw new Error(await parseError(response));
            return await response.json();
        },

        async getTeam() {
            const response = await fetch(`${API_URL}/team/`, {
                headers: authHeaders(),
            });
            if (!response.ok) throw new Error(await parseError(response));
            return await response.json();
        },

        async createOrganization(name) {
            const response = await fetch(`${API_URL}/team/create`, {
                method: 'POST',
                headers: authHeaders({ 'Content-Type': 'application/json' }),
                body: JSON.stringify({ name }),
            });
            if (!response.ok) throw new Error(await parseError(response));
            return await response.json();
        },

        async inviteTeamMember(email, role = 'viewer') {
            const response = await fetch(`${API_URL}/team/invite`, {
                method: 'POST',
                headers: authHeaders({ 'Content-Type': 'application/json' }),
                body: JSON.stringify({ email, role }),
            });
            if (!response.ok) throw new Error(await parseError(response));
            return await response.json();
        },

        async joinTeam(token) {
            const response = await fetch(`${API_URL}/team/join/${token}`, {
                method: 'POST',
                headers: authHeaders(),
            });
            if (!response.ok) throw new Error(await parseError(response));
            return await response.json();
        },

        async updateTeamMemberRole(memberId, role) {
            const response = await fetch(`${API_URL}/team/members/${memberId}`, {
                method: 'PATCH',
                headers: authHeaders({ 'Content-Type': 'application/json' }),
                body: JSON.stringify({ role }),
            });
            if (!response.ok) throw new Error(await parseError(response));
            return await response.json();
        },

        async removeTeamMember(memberId) {
            const response = await fetch(`${API_URL}/team/members/${memberId}`, {
                method: 'DELETE',
                headers: authHeaders(),
            });
            if (!response.ok) throw new Error(await parseError(response));
            return await response.json();
        },

        async cancelTeamInvite(inviteId) {
            const response = await fetch(`${API_URL}/team/invites/${inviteId}`, {
                method: 'DELETE',
                headers: authHeaders(),
            });
            if (!response.ok) throw new Error(await parseError(response));
            return await response.json();
        },
    };
}
