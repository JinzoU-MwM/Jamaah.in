/**
 * Global reactive stores shared across all modules.
 * Keep this small — page-local state stays in each component.
 */
let _currentUser = $state(null);
let _activePackageId = $state(null);

export function getCurrentUser() {
    return _currentUser;
}

export function setCurrentUser(user) {
    _currentUser = user;
}

export function getActivePackageId() {
    return _activePackageId;
}

export function setActivePackageId(id) {
    _activePackageId = id;
}
