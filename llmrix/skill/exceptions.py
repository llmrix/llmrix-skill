class GitSkillError(Exception):
    """Base exception for gitskill library"""
    pass

class SkillNotFoundError(GitSkillError):
    """Raised when a skill is not found in storage"""
    pass

class VersionNotFoundError(GitSkillError):
    """Raised when a specific version of a skill is not found"""
    pass

class PermissionDeniedError(GitSkillError):
    """Raised when a user lacks permission to modify a skill"""
    pass

class ValidationError(GitSkillError):
    """Raised when skill metadata or code is invalid"""
    pass

class GitOperationError(GitSkillError):
    """Raised when a git command fails"""
    pass
